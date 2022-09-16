import logging
import os
from typing import List

from dipdup.context import HookContext
from rarible_marketplace_indexer.jobs.metadata import process_metadata

from rarible_marketplace_indexer.models import Collection
from rarible_marketplace_indexer.models import IndexEnum


async def process_missing_metadata_for_collection(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("collection_metadata")
    logger.info("Starting collection metadata job")
    missing_meta_collections: List[Collection] = await Collection.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(1000)
    for collection in missing_meta_collections:
        metadata = await process_metadata(ctx, IndexEnum.COLLECTION, collection.contract)
        if metadata is None:
            collection.metadata_retries = collection.metadata_retries + 1
            logger.warning(f"Metadata not found for {collection.contract} (retries {collection.metadata_retries})")
        else:
            await ctx.update_contract_metadata(os.getenv('NETWORK'), collection.contract, metadata)
            collection.metadata_synced = True
            logger.info(
                f"Successfully saved metadata for {collection.contract} (retries {collection.metadata_retries})"
            )
        await collection.save()
