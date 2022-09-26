import asyncio
import json
import logging
import os
from asyncio import create_task
from asyncio import gather
from collections import deque
from datetime import datetime
from typing import Deque
from typing import List

import tortoise

from dipdup.context import HookContext

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum, Token
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.models import TokenMetadata
from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport

from rarible_marketplace_indexer.utils.rarible_utils import date_pattern

pending_tasks = deque()
metadata_to_update: Deque[TokenMetadata] = deque()
logger = logging.getLogger("token_metadata")
logger.setLevel("INFO")


async def process_metadata_for_token(ctx: HookContext, token_meta: TokenMetadata):
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


async def boostrap_token_metadata(meta: TokenMetadata):
    logger.info(f"Bootstrapped metadata for token {meta.contract}:{meta.token_id}")
    try:
        await meta.save(force_create=True)
    except tortoise.exceptions.IntegrityError:
        await meta.save(force_update=True)



async def process_token_metadata(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger.info("Running token metadata job")
    index = await IndexingStatus.get_or_none(index=IndexEnum.NFT_METADATA)
    if index is None:
        transport = AIOHTTPTransport(url=ctx.get_metadata_datasource("metadata").url + "/v1/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        done = False
        offset = 0
        while not done:
            query = gql(
                """
                    query MyQuery {
                      token_metadata(
                        where: {metadata: {_is_null: false}, network: {_eq: "%network%"}}
                        limit: 1000
                        offset: %offset%
                      ) {
                        contract
                        token_id
                        metadata
                      }
                    }
            """.replace("%network%", os.getenv("NETWORK")).replace("%offset%", str(offset))
            )
            offset += 1000
            try:
                result = await client.execute_async(query)
            except asyncio.exceptions.TimeoutError:
                result = await client.execute_async(query)

            data = result.get("token_metadata")
            if len(data) == 0:
                done = True
            for meta in data:
                pending_tasks.append(create_task(boostrap_token_metadata(TokenMetadata(
                    id=Token.get_id(meta.get("contract"), meta.get("token_id")),
                    contract=meta.get("contract"),
                    token_id=meta.get("token_id"),
                    metadata=meta.get("metadata"),
                    metadata_synced=True,
                    metadata_retries=0,
                    db_updated_at=datetime.now().strftime(date_pattern)
                ))))
            await gather(*pending_tasks)

        await IndexingStatus.create(index=IndexEnum.NFT_METADATA, last_level="DONE")

    done = False
    offset = 0
    while not done:
        unsynced_tokens_metadata: List[TokenMetadata] = (
            await TokenMetadata.filter(
                metadata_synced=False,
                metadata_retries__lt=5,
            )
            .limit(100)
            .offset(offset)
        )
        offset += 100
        if len(unsynced_tokens_metadata) == 0:
            done = True
        for meta in unsynced_tokens_metadata:
            pending_tasks.append(create_task(process_metadata_for_token(ctx, meta)))
        await gather(*pending_tasks)
    logger.info("Token metadata job finished")
