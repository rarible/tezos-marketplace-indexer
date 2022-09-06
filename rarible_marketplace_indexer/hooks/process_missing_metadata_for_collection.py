import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Collection, IndexEnum
from rarible_marketplace_indexer.utils.rarible_utils import process_metadata


async def process_missing_metadata_for_collection(
    ctx: HookContext,
) -> None:
    logger = logging.getLogger("metadata_daemon")
    logger.info("starting metadata daemon")
    print("test")
    missing_meta_collections: List[Collection] = await Collection.filter(
        metadata=None,
        metadata_retries__lt=5,
    ).limit(100)
    for collection in missing_meta_collections:
        collection.metadata = await process_metadata(ctx, IndexEnum.COLLECTION, collection.contract)
        if collection.metadata is None:
            collection.metadata_retries = collection.metadata_retries + 1
        await collection.save()
        print(f"saved collection {collection.contract} with retries {collection.metadata_retries}")
