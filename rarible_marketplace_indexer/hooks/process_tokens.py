import json
import logging
from asyncio import create_task, gather
from collections import deque
from typing import List, Deque

from dipdup.context import HookContext

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum, Royalties
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata
from rarible_marketplace_indexer.royalties.royalties import fetch_royalties
from rarible_marketplace_indexer.utils.rarible_utils import get_json_parts

pending_tasks = deque()
tokens_to_update: Deque[Token] = deque()
metadata_to_update: Deque[TokenMetadata] = deque()
royalties_to_update: Deque[Royalties] = deque()


async def process_token_metadata(ctx: HookContext, token: Token):
    logger = logging.getLogger("token_metadata")
    metadata = await process_metadata(ctx, IndexEnum.NFT, f"{token.contract}:{token.token_id}")
    if metadata is None:
        token.metadata_retries = token.metadata_retries + 1
        token.metadata_synced = False
        logger.warning(
            f"Metadata not found for {token.contract}:{token.token_id} (retries {token.metadata_retries})"
        )
    else:
        try:
            token_meta = await TokenMetadata.get_or_none(
                id=token.id,
            )
            token_meta.metadata = json.dumps(metadata)
            token.metadata_synced = True
            token.metadata_retries = token.metadata_retries
            metadata_to_update.append(token_meta)
            logger.info(
                f"Successfully saved metadata for {token.contract}:{token.token_id} (retries {token.metadata_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save token metadata for {token.contract}:{token.token_id}: {ex}")
            token.metadata_retries = token.metadata_retries + 1
            token.metadata_synced = False
    tokens_to_update.append(token)


async def process_token_royalties(ctx: HookContext, token: Token):
    logger = logging.getLogger("token_royalties")
    royalties = await fetch_royalties(ctx, token.contract, token.token_id)
    if royalties is None:
        token.royalties_retries = token.royalties_retries + 1
        token.royalties_synced = False
        logger.warning(
            f"Royalties not found for {token.contract}:{token.token_id} (retries {token.royalties_retries})"
        )
    else:
        try:
            token_royalties = await Royalties.get_or_none(
                id=token.id,
            )
            token_royalties.parts = get_json_parts(royalties)
            token.royalties_synced = True
            token.royalties_retries = token.royalties_retries
            royalties_to_update.append(token_royalties)
            logger.info(
                f"Successfully saved royalties for {token.contract}:{token.token_id} (retries {token.royalties_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save royalties for {token.contract}:{token.token_id}: {ex}")
            token.royalties_retries = token.royalties_retries + 1
            token.royalties_synced = False
    tokens_to_update.append(token)

async def process_tokens(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("token")
    logger.info("Running token job")
    unsynced_tokens: List[Token] = await Token.filter(
        metadata_synced=False,
        royalties_synced=False,
        metadata_retries__lt=5,
        royalties_retries__lt=5,
    ).limit(1000)
    if len(unsynced_tokens) > 0:
        for token in unsynced_tokens:
            pending_tasks.append(create_task(process_token_metadata(ctx, token)))
            pending_tasks.append(create_task(process_token_royalties(ctx, token)))
        await gather(*pending_tasks)
        await Token.bulk_update(tokens_to_update, fields=["metadata_synced", "royalties_synced", "metadata_retries", "royalties_retries"])
        await TokenMetadata.bulk_update(metadata_to_update, fields=["metadata"])
        await Royalties.bulk_update(royalties_to_update, fields=["parts"])
    logger.info("Token job finished")
