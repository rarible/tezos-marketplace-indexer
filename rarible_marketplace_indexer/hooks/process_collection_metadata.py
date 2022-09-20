import json
import logging
from asyncio import create_task, gather
from collections import deque
from typing import List

from dipdup.context import HookContext
from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import CollectionMetadata, IndexingStatus
from rarible_marketplace_indexer.models import IndexEnum

pending_tasks = deque()


async def process_metadata_for_collection(ctx: HookContext, collection_meta: CollectionMetadata):
    logger = logging.getLogger("collection_metadata")
    metadata = await process_metadata(ctx, IndexEnum.COLLECTION, collection_meta.contract)
    if metadata is None:
        collection_meta.metadata_retries = collection_meta.metadata_retries + 1
        collection_meta.metadata_synced = False
        logger.warning(f"Metadata not found for {collection_meta.contract} (retries {collection_meta.metadata_retries})")
    else:
        try:
            collection_meta.metadata_synced = True
            collection_meta.metadata_retries = collection_meta.metadata_retries
            collection_meta.metadata = json.dumps(metadata)
            logger.info(
                f"Successfully saved metadata for {collection_meta.contract} (retries {collection_meta.metadata_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save collection metadata for {collection_meta.contract}: {ex}")
            collection_meta.metadata_retries = collection_meta.metadata_retries + 1
            collection_meta.metadata_synced = False
    await collection_meta.save()


async def boostrap_collection_metadata(ctx: HookContext, meta: CollectionMetadata):
    logger = logging.getLogger("boostrap_token_metadata")
    metadata = await ctx.get_metadata_datasource("metadata").get_contract_metadata(meta.contract)
    if metadata is not None:
        logger.info(f"boostraped collection {meta.contract}")
        meta.metadata = metadata
        meta.metadata_synced = True
        await meta.save()


async def process_collection_metadata(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("collection_metadata")
    logger.info("Running collection metadata job")
    index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION_METADATA)
    if index is None:
        done = False
        offset = 0
        while not done:
            unsynced_tokens_metadata: List[CollectionMetadata] = await CollectionMetadata.filter(
                metadata_synced=False,
                metadata_retries__lt=5,
            ).limit(1000).offset(offset)
            offset += 1000
            if len(unsynced_tokens_metadata) == 0:
                done = True
            for meta in unsynced_tokens_metadata:
                pending_tasks.append(create_task(boostrap_collection_metadata(ctx, meta)))
            await gather(*pending_tasks)

        await IndexingStatus.create(index=IndexEnum.COLLECTION_METADATA, last_level="DONE")

    missing_meta_collections: List[CollectionMetadata] = await CollectionMetadata.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(100)
    for collection_meta in missing_meta_collections:
        pending_tasks.append(create_task(process_metadata_for_collection(ctx, collection_meta)))
    await gather(*pending_tasks)
    logger.info("Collection metadata job finished")
