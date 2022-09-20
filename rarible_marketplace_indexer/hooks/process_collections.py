import json
import logging
from asyncio import create_task, gather
from collections import deque
from typing import List, Deque

from dipdup.context import HookContext
from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import Collection
from rarible_marketplace_indexer.models import CollectionMetadata
from rarible_marketplace_indexer.models import IndexEnum

pending_tasks = deque()
collections_to_update: Deque[Collection] = deque()
metadata_to_update: Deque[CollectionMetadata] = deque()


async def process_collection_metadata(ctx: HookContext, collection: Collection):
    logger = logging.getLogger("collection_metadata")
    metadata = await process_metadata(ctx, IndexEnum.COLLECTION, collection.contract)
    if metadata is None:
        collection.metadata_retries = collection.metadata_retries + 1
        collection.metadata_synced = False
        logger.warning(f"Metadata not found for {collection.contract} (retries {collection.metadata_retries})")
    else:
        try:
            collection_meta = await CollectionMetadata.get_or_none(contract=collection.contract)
            collection.metadata_synced = True
            collection.metadata_retries = collection.metadata_retries
            collection_meta.metadata = json.dumps(metadata)
            metadata_to_update.append(collection_meta)
            logger.info(
                f"Successfully saved metadata for {collection.contract} (retries {collection.metadata_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save collection metadata for {collection.contract}: {ex}")
            collection.metadata_retries = collection.metadata_retries + 1
            collection.metadata_synced = False
    collections_to_update.append(collection)


async def process_collections(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("collection_metadata")
    logger.info("Running collection metadata job")
    missing_meta_collections: List[Collection] = await Collection.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(1000)
    for collection in missing_meta_collections:
        pending_tasks.append(create_task(process_collection_metadata(ctx, collection)))
    await gather(*pending_tasks)
    await Collection.bulk_update(collections_to_update, fields=["metadata_synced", "metadata_retries"])
    await CollectionMetadata.bulk_update(metadata_to_update, fields=["metadata"])
    logger.info("Collection metadata job finished")
