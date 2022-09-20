import json
import logging
from asyncio import create_task
from asyncio import gather
from collections import deque
from typing import Deque
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.models import TokenMetadata

pending_tasks = deque()
metadata_to_update: Deque[TokenMetadata] = deque()


async def process_metadata_for_token(ctx: HookContext, token_meta: TokenMetadata):
    logger = logging.getLogger("token_metadata")
    metadata = await process_metadata(ctx, IndexEnum.NFT, f"{token_meta.contract}:{token_meta.token_id}")
    if metadata is None:
        token_meta.metadata_retries = token_meta.metadata_retries + 1
        token_meta.metadata_synced = False
        logger.warning(
            f"Metadata not found for {token_meta.contract}:{token_meta.token_id} "
            f"(retries {token_meta.metadata_retries})"
        )
    else:
        try:
            token_meta.metadata = json.dumps(metadata)
            token_meta.metadata_synced = True
            token_meta.metadata_retries = token_meta.metadata_retries
            logger.info(
                f"Successfully saved metadata for {token_meta.contract}:{token_meta.token_id} "
                f"(retries {token_meta.metadata_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save token metadata for {token_meta.contract}:{token_meta.token_id}: {ex}")
            token_meta.metadata_retries = token_meta.metadata_retries + 1
            token_meta.metadata_synced = False
    await token_meta.save()


async def boostrap_token_metadata(ctx: HookContext, meta: TokenMetadata):
    logger = logging.getLogger("boostrap_token_metadata")
    metadata = await ctx.get_metadata_datasource("metadata").get_token_metadata(meta.contract, meta.token_id)
    if metadata is not None:
        if metadata.get("token_info") is None and metadata.get("token_id") is None:
            logger.info(f"boostraped token {meta.contract}:{meta.token_id}")
            meta.metadata = metadata
            meta.metadata_synced = True
            await meta.save()


async def process_token_metadata(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("token_metadata")
    logger.info("Running token metadata job")
    index = await IndexingStatus.get_or_none(index=IndexEnum.NFT_METADATA)
    if index is None:
        done = False
        offset = 0
        while not done:
            unsynced_tokens_metadata: List[TokenMetadata] = (
                await TokenMetadata.filter(
                    metadata_synced=False,
                    metadata_retries__lt=5,
                )
                .limit(1000)
                .offset(offset)
            )
            offset += 1000
            if len(unsynced_tokens_metadata) == 0:
                done = True
            for meta in unsynced_tokens_metadata:
                pending_tasks.append(create_task(boostrap_token_metadata(ctx, meta)))
            await gather(*pending_tasks)

        await IndexingStatus.create(index=IndexEnum.NFT_METADATA, last_level="DONE")

    unsynced_tokens_metadata: List[TokenMetadata] = await TokenMetadata.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(100)
    if len(unsynced_tokens_metadata) > 0:
        for token in unsynced_tokens_metadata:
            pending_tasks.append(create_task(process_metadata_for_token(ctx, token)))
        await gather(*pending_tasks)
    logger.info("Token metadata job finished")
