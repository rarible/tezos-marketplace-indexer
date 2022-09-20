import json
import logging
from asyncio import create_task, gather
from collections import deque
from typing import List, Any, Deque

from dipdup.context import HookContext

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata

pending_tasks = deque()
tokens_to_update: Deque[Token] = deque()
metadata_to_update: Deque[TokenMetadata] = deque()


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


async def process_metadata_for_tokens(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("token_metadata")
    logger.info("Running token metadata job")
    missing_meta_tokens: List[Token] = await Token.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(1000)
    for token in missing_meta_tokens:
        pending_tasks.append(create_task(process_token_metadata(ctx, token)))
    await gather(*pending_tasks)
    await Token.bulk_update(tokens_to_update, fields=["metadata_synced", "metadata_retries"])
    await TokenMetadata.bulk_update(metadata_to_update, fields=["metadata"])
    logger.info("Token metadata job finished")
