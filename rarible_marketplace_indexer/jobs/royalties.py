import logging
from typing import Dict, Any

import requests
from requests import Response

from dipdup.context import DipDupContext
from rarible_marketplace_indexer.jobs.metadata import get_token_metadata
from rarible_marketplace_indexer.models import TokenTransfer, ActivityTypeEnum
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part

logger = logging.getLogger("royalties")


async def process_royalties(ctx: DipDupContext, contract: str, token_id: str) -> [Part]:
    known_addresses: Dict[str, str] = ctx.config.custom.get("royalties")
    if known_addresses is None:
        raise Exception("Missing royalties configuration")

    if contract == known_addresses.get("hen"):
        logger.info(f"Token {contract}:{token_id} royalties pattern is HEN")
        return await get_hen_royalties(ctx, known_addresses.get("hen_royalties"), token_id)
    elif contract == known_addresses.get("kalamint"):
        logger.info(f"Token {contract}:{token_id} royalties pattern is KALAMINT (public collection)")
        return await get_kalamint_royalties(contract, token_id)
    elif contract == known_addresses.get("fxhash_v1"):
        logger.info(f"Token {contract}:{token_id} royalties pattern is FXHASH_V1")
        return await get_fxhash_v1_royalties(token_id)
    elif contract == known_addresses.get("fxhash_v2"):
        logger.info(f"Token {contract}:{token_id} royalties pattern is FXHASH_V2")
        return await get_fxhash_v2_royalties(token_id)
    elif contract == known_addresses.get("versum"):
        logger.info(f"Token {contract}:{token_id} royalties pattern is VERSUM")
        return await get_versum_royalties(token_id)
    elif contract in [known_addresses.get("bidou_8x8"), known_addresses.get("bidou_24x24")]:
        logger.info("Token $contract:$tokenId royalties pattern is 8Bidou")
        return await get_bidou_royalties(contract, token_id)

    royalties = await get_rarible_royalties(contract, token_id)

    if len(royalties) > 0:
        logger.info(f"Token {contract}:{token_id} royalties pattern is RARIBLE")
        return royalties

    royalties = await get_kalamint_royalties(contract, token_id)

    if len(royalties) > 0:
        logger.info(f"Token {contract}:{token_id} royalties pattern is KALAMINT (private collection)")
        return royalties

    token_metadata = await get_token_metadata(ctx, f"{contract}:{token_id}")
    if token_metadata is not None:
        metadata_royalties = token_metadata.get("royalties")
        if metadata_royalties is not None:
            shares = metadata_royalties.get("shares")
            decimals = metadata_royalties.get("decimals")
            if shares is not None and decimals is not None:
                logger.info(f"Token {contract}:{token_id} royalties pattern is OBJKT")
                return await get_objkt_royalties(contract, token_id, metadata_royalties)
        attributes = token_metadata.get("attributes")
        if attributes is not None:
            royalties = await get_sweet_io_royalties(contract, token_id, token_metadata)
            if len(royalties) > 0:
                return royalties

    royalties = await get_royalties_from_royalties_manager(contract, token_id)
    if len(royalties) > 0:
        return royalties

    royalties = await get_embedded_royalties(token_metadata, f"{contract}:{token_id}")
    if len(royalties) > 0:
        return royalties

    mint: TokenTransfer = (
        await TokenTransfer.filter(
            contract=contract,
            token_id=token_id,
            type=ActivityTypeEnum.TOKEN_MINT
        )
        .order_by("+id")
        .first()
    )

    royalties = [Part(part_account=mint.to_address, part_value=0)]

    return royalties


async def get_objkt_royalties(contract: str, token_id: str, royalties):
    pass


async def get_hen_royalties(ctx: DipDupContext, contract, token_id: str):
    response = await get_key_for_big_map(ctx, contract, "royalties", token_id)
    try:
        royalties_map = response.json()
        royalties: dict[str, Any] = royalties_map.get("value")
        return [Part(part_account=royalties.get("issuer"), part_value=int(royalties.get("royalties")) * 10)]
    except Exception as ex:
        logger.error(f"Could not fetch HEN royalties for {contract}:{token_id}: {ex}")
        return []


async def get_kalamint_royalties(contract: str, token_id: str):
    pass


async def get_fxhash_v1_royalties(token_id: str):
    pass


async def get_fxhash_v2_royalties(token_id: str):
    pass


async def get_versum_royalties(token_id: str):
    pass


async def get_bidou_royalties(contract: str, token_id: str):
    pass


async def get_rarible_royalties(contract: str, token_id: str):
    pass


async def get_sweet_io_royalties(contract: str, token_id: str, ipfs_data: dict):
    pass


async def get_royalties_from_royalties_manager(contract: str, token_id: str):
    pass


async def get_embedded_royalties(token_metadata: dict[str, Any], token_id: str):
    pass


async def get_key_for_big_map(ctx: DipDupContext, contract: str, name: str, key: str) -> Response:
    return requests.get(
                        f'{ctx.config.get_tzkt_datasource("tzkt").url}'
                        f'/v1/contracts/{contract}/bigmaps/{name}/keys/'
                        f'{key}'
    )
