import asyncio
import json
import logging
import os
from asyncio import create_task
from asyncio import gather
from collections import deque
from datetime import datetime
from typing import List

import tortoise
from dipdup.context import HookContext
from gql import Client
from gql import gql
from gql.transport.aiohttp import AIOHTTPTransport

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import CollectionMetadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern

pending_tasks = deque()
logger = logging.getLogger("collection_metadata")
logger.setLevel("INFO")


async def process_metadata_for_collection(ctx: HookContext, collection_meta: CollectionMetadata):
    metadata = await process_metadata(ctx, IndexEnum.COLLECTION, collection_meta.contract)
    if metadata is None:
        collection_meta.metadata_retries = collection_meta.metadata_retries + 1
        collection_meta.metadata_synced = False
        logger.warning(
            f"Metadata not found for {collection_meta.contract} (retries {collection_meta.metadata_retries})"
        )
    else:
        try:
            collection_meta.metadata_synced = True
            collection_meta.metadata_retries = collection_meta.metadata_retries
            collection_meta.metadata = json.dumps(metadata)
            logger.info(
                f"Successfully saved metadata for {collection_meta.contract} "
                f"(retries {collection_meta.metadata_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save collection metadata for {collection_meta.contract}: {ex}")
            collection_meta.metadata_retries = collection_meta.metadata_retries + 1
            collection_meta.metadata_synced = False
    await collection_meta.save()


async def boostrap_collection_metadata(meta: CollectionMetadata):
    logger.info(f"Bootstrapped metadata for collection {meta.contract}")
    try:
        await meta.save(force_create=True)
    except tortoise.exceptions.IntegrityError:
        await meta.save(force_update=True)


async def process_collection_metadata(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger.info("Running collection metadata job")
    index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION_METADATA)
    if index is None:
        transport = AIOHTTPTransport(url=ctx.get_metadata_datasource("metadata").url + "/v1/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        done = False
        offset = 0
        while not done:
            query = gql(
                """
                    query MyQuery {
                      contract_metadata(
                        limit: 1000
                        offset: %offset%
                        where: {metadata: {_is_null: false}, network: {_eq: "%network%"}}
                      ) {
                        contract
                        metadata
                      }
                    }
            """.replace(
                    "%network%", os.getenv("NETWORK")
                ).replace(
                    "%offset%", str(offset)
                )
            )
            offset += 1000
            try:
                result = await client.execute_async(query)
            except asyncio.exceptions.TimeoutError:
                result = await client.execute_async(query)
            data = result.get("contract_metadata")
            if len(data) == 0:
                done = True
            for meta in data:
                pending_tasks.append(
                    create_task(
                        boostrap_collection_metadata(
                            CollectionMetadata(
                                contract=meta.get("contract"),
                                metadata=meta.get("metadata"),
                                metadata_synced=True,
                                metadata_retries=0,
                                db_updated_at=datetime.now().strftime(date_pattern),
                            )
                        )
                    )
                )
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
