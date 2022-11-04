import json
import logging
import math
from typing import Any
from typing import Dict

from dipdup.context import DipDupContext

from rarible_marketplace_indexer.metadata.metadata import get_token_metadata
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata
from rarible_marketplace_indexer.models import TokenTransfer
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.utils.rarible_utils import get_bidou_data
from rarible_marketplace_indexer.utils.rarible_utils import get_key_for_big_map
from rarible_marketplace_indexer.utils.rarible_utils import get_royalties_manager_big_map_key_hash
from rarible_marketplace_indexer.utils.rarible_utils import get_token_id_big_map_key_hash

logger = logging.getLogger("royalties")
logger.setLevel("INFO")


async def get_objkt_royalties(contract: str, token_id: str, data: dict[str, Any]):
    try:
        shares: dict[str, Any] = data.get("shares")
        shareholders = shares.keys()
        decimals: dict[str, Any] = data.get("decimals")
        royalties: [Part] = []
        for shareholder in shareholders:
            percentage = int(int(data.get("shares").get(shareholder)) * math.pow(10, int(decimals) * -1) * 10000)
            royalties.append(Part(part_account=shareholder, part_value=percentage))
        return royalties
    except Exception as ex:
        logger.debug(f"Could not fetch OBJKT royalties for {contract}:{token_id}: {ex}")
        return []


async def get_hen_royalties(ctx: DipDupContext, contract, token_id: str):
    try:
        response = await get_key_for_big_map(ctx, contract, "royalties", get_token_id_big_map_key_hash(token_id))
        royalties: dict[str, Any] = response.get("value")
        return [Part(part_account=royalties.get("issuer"), part_value=int(royalties.get("royalties")) * 10)]
    except Exception as ex:
        logger.debug(f"Could not fetch HEN royalties for {contract}:{token_id}: {ex}")
        return []


async def get_kalamint_royalties(ctx: DipDupContext, contract: str, token_id: str):
    try:
        response = await get_key_for_big_map(ctx, contract, "tokens", get_token_id_big_map_key_hash(token_id))
        royalties: dict[str, Any] = response.get("value")
        return [Part(part_account=royalties.get("creator"), part_value=int(royalties.get("creator_royalty")) * 100)]
    except Exception as ex:
        logger.debug(f"Could not fetch KALAMINT royalties for {contract}:{token_id}: {ex}")
        return []


async def get_fxhash_v1_royalties(ctx: DipDupContext, fxhash_v1: str, fxhash_v1_manager: str, token_id: str):
    try:
        key_response = await get_key_for_big_map(ctx, fxhash_v1, "token_data", get_token_id_big_map_key_hash(token_id))
        royalties = key_response.get("value")
        author_response = await get_key_for_big_map(
            ctx, fxhash_v1_manager, "ledger", get_token_id_big_map_key_hash(royalties.get("issuer_id"))
        )
        author = author_response.get("value")
        return [Part(part_account=author.get("author"), part_value=int(royalties.get("royalties")) * 10)]
    except Exception as ex:
        logger.debug(f"Could not fetch FXHASH V1 royalties for {fxhash_v1}:{token_id}: {ex}")
        return []
    pass


async def get_fxhash_v2_royalties(ctx: DipDupContext, contract: str, token_id: str):
    try:
        response = await get_key_for_big_map(ctx, contract, "token_data", get_token_id_big_map_key_hash(token_id))
        royalties_data: dict[str, Any] = response.get("value")
        amount = royalties_data.get("royalties")
        splits: [dict[str, Any]] = royalties_data.get("royalties_split")
        royalties: [Part] = []
        for split in splits:
            royalties.append(
                Part(part_account=split.get("address"), part_value=int(int(amount) * int(split.get("pct")) / 100))
            )
        return royalties
    except Exception as ex:
        logger.debug(f"Could not fetch FXHASH V2 royalties for {contract}:{token_id}: {ex}")
        return []


async def get_versum_royalties(ctx: DipDupContext, contract: str, token_id: str):
    try:
        response = await get_key_for_big_map(ctx, contract, "token_extra_data", get_token_id_big_map_key_hash(token_id))
        royalties: dict[str, Any] = response.get("value")
        return [Part(part_account=royalties.get("minter"), part_value=int(royalties.get("royalty")) * 10)]
    except Exception as ex:
        logger.debug(f"Could not fetch VERSUM royalties for {contract}:{token_id}: {ex}")
        return []


async def get_bidou_royalties(ctx: DipDupContext, contract: str, token_id: str, bidou_royalties: Dict[str, int]):
    royalties: [Part] = []
    try:
        data = await get_bidou_data(ctx, contract, token_id)
        creater = data.get("creater")
        creator = data.get("creator")
        part_account = creater if creater is not None else creator
        royalties.append(Part(part_account=part_account, part_value=bidou_royalties.get(contract)))
        return royalties
    except Exception as ex:
        logger.debug(f"Could not fetch BIDOU royalties for {contract}:{token_id}: {ex}")
        return []


async def get_rarible_royalties(ctx: DipDupContext, contract: str, token_id: str):
    try:
        response = await get_key_for_big_map(ctx, contract, "royalties", get_token_id_big_map_key_hash(token_id))
        royalties_list: [dict[str, Any]] = response.get("value")
        royalties: [Part] = []
        for royalty in royalties_list:
            royalties.append(Part(part_account=royalty.get("partAccount"), part_value=int(royalty.get("partValue"))))
        return royalties
    except Exception as ex:
        logger.debug(f"Could not fetch RARIBLE royalties for {contract}:{token_id}: {ex}")
        return []


async def get_sweet_io_royalties(contract: str, token_id: str, data: dict[str, Any]):
    try:
        attributes: [dict[str, Any]] = data.get("attributes")
        royalties: [Part] = []
        recipient = None
        share = None
        for attribute in attributes:
            att: dict[str, Any] = attribute
            name = att.get("name")
            if name is not None:
                if name == "fee_recipient":
                    recipient = att.get("value")
                if name == "seller_fee_basis_points":
                    share = att.get("value")
        if recipient is not None and share is not None:
            logger.debug(f"Token {contract}:{token_id} royalties pattern is SWEET IO")
            royalties.append(Part(part_account=recipient, part_value=share))
        return royalties
    except Exception as ex:
        logger.debug(f"Could not fetch SWEET IO royalties for {contract}:{token_id}: {ex}")
        return []


async def get_royalties_from_royalties_manager(
    ctx: DipDupContext, royalties_manager: str, contract: str, token_id: str
):
    royalties: [Part] = []
    royalties_map: [dict[str, Any]] | None = None
    try:
        response_with_token_id = await get_key_for_big_map(
            ctx, royalties_manager, "royalties", get_royalties_manager_big_map_key_hash(contract, token_id)
        )
        royalties_map = response_with_token_id.get("value")
    except Exception as ex:
        logger.debug(f"Could not fetch Royalties Manager royalties (with token id) for {contract}:{token_id}: {ex}")
    if royalties_map is None:
        try:
            response_without_token_id = await get_key_for_big_map(
                ctx, royalties_manager, "royalties", get_royalties_manager_big_map_key_hash(contract, None)
            )
            royalties_map = response_without_token_id.get("value")
        except Exception as ex:
            logger.debug(
                f"Could not fetch Royalties Manager royalties (without token id) for {contract}:{token_id}: {ex}"
            )
    if royalties_map is not None:
        for royalty in royalties_map:
            royalties.append(Part(part_account=royalty.get("partAccount"), part_value=royalty.get("partValue")))
    return royalties


async def get_embedded_royalties(token_metadata: dict[str, Any], id: str):
    royalties: [Part] = []
    try:
        metadata = token_metadata.get("token_info")
        embedded_royalty: str = metadata.get("royalties")
        decoded_embedded_royalty: dict[str, Any] = json.loads(bytes.fromhex(embedded_royalty).decode("utf-8"))
        shares = decoded_embedded_royalty.get("shares")
        decimals = int(decoded_embedded_royalty.get("decimals"))
        decimals = math.pow(10, decimals)
        for share in shares:
            royalties.append(Part(part_account=share, part_value=decimals))
    except Exception as ex:
        logger.debug(f"Could not fetch embedded royalties for {id}: {ex}")
    return []


async def fetch_royalties(ctx: DipDupContext, contract: str, token_id: str) -> [Part]:
    known_addresses: Dict[str, str] = ctx.config.custom.get("royalties")
    if known_addresses is None:
        raise Exception("Missing royalties configuration")
    bidou_royalties: Dict[str, int] = {known_addresses.get("bidou_8x8"): 1000, known_addresses.get("bidou_24x24"): 1500}

    if contract == known_addresses.get("hen"):
        logger.debug(f"Token {contract}:{token_id} royalties pattern is HEN")
        return await get_hen_royalties(ctx, known_addresses.get("hen_royalties"), token_id)
    elif contract == known_addresses.get("kalamint"):
        logger.debug(f"Token {contract}:{token_id} royalties pattern is KALAMINT (public collection)")
        return await get_kalamint_royalties(ctx, contract, token_id)
    elif contract == known_addresses.get("fxhash_v1"):
        logger.debug(f"Token {contract}:{token_id} royalties pattern is FXHASH_V1")
        return await get_fxhash_v1_royalties(ctx, contract, known_addresses.get("fxhash_v1_manager"), token_id)
    elif contract == known_addresses.get("fxhash_v2"):
        logger.debug(f"Token {contract}:{token_id} royalties pattern is FXHASH_V2")
        return await get_fxhash_v2_royalties(ctx, contract, token_id)
    elif contract == known_addresses.get("versum"):
        logger.debug(f"Token {contract}:{token_id} royalties pattern is VERSUM")
        return await get_versum_royalties(ctx, contract, token_id)
    elif contract in [
        known_addresses.get("bidou_8x8"),
        known_addresses.get("bidou_24x24"),
        known_addresses.get("bidou_24x24_color"),
    ]:
        logger.debug("Token $contract:$tokenId royalties pattern is 8Bidou")
        return await get_bidou_royalties(ctx, contract, token_id, bidou_royalties)

    royalties = await get_rarible_royalties(ctx, contract, token_id)

    if len(royalties) > 0:
        logger.debug(f"Token {contract}:{token_id} royalties pattern is RARIBLE")
        return royalties

    royalties = await get_kalamint_royalties(ctx, contract, token_id)

    if len(royalties) > 0:
        logger.debug(f"Token {contract}:{token_id} royalties pattern is KALAMINT (private collection)")
        return royalties

    token_metadata = await TokenMetadata.get_or_none(id=Token.get_id(contract, token_id))
    if token_metadata is None or token_metadata is not None and token_metadata.metadata is None:
        token_metadata = await get_token_metadata(ctx, f"{contract}:{token_id}")
    else:
        token_metadata = token_metadata.metadata
    if token_metadata is not None:
        try:
            if type(token_metadata) is bytes:
                parsed_data = json.loads(str(token_metadata))
                token_metadata = parsed_data
            else:
                token_metadata_royalties = token_metadata.get("royalties")
                if type(token_metadata_royalties) is str:
                    metadata_royalties = json.loads(token_metadata_royalties)
                else:
                    metadata_royalties = token_metadata_royalties
                if metadata_royalties is not None:
                    shares = metadata_royalties.get("shares")
                    decimals = metadata_royalties.get("decimals")
                    if shares is not None and decimals is not None:
                        logger.debug(f"Token {contract}:{token_id} royalties pattern is OBJKT")
                        return await get_objkt_royalties(contract, token_id, metadata_royalties)
                attributes = token_metadata.get("attributes")
                if attributes is not None:
                    royalties = await get_sweet_io_royalties(contract, token_id, token_metadata)
                    if len(royalties) > 0:
                        return royalties
        except Exception as ex:
            logger.debug(f"Could not parse royalties from metadata for {contract}:{token_id}: {ex}")

    royalties = await get_royalties_from_royalties_manager(
        ctx, known_addresses.get("royalties_manager"), contract, token_id
    )
    if len(royalties) > 0:
        return royalties

    royalties = await get_embedded_royalties(token_metadata, f"{contract}:{token_id}")
    if len(royalties) > 0:
        return royalties

    mint: TokenTransfer = (
        await TokenTransfer.filter(contract=contract, token_id=token_id, type=ActivityTypeEnum.TOKEN_MINT)
        .order_by("date")
        .first()
    )

    royalties = [Part(part_account=mint.to_address, part_value=0)]

    return royalties
