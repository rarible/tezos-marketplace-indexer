import asyncio
import json
import logging
import os
from multiprocessing import Pool

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.utils.rarible_utils import import_legacy_order


async def import_legacy_orders(
    ctx: HookContext,
) -> None:
    logger = logging.getLogger('dipdup.legacy')

    index = await IndexingStatus.get_or_none(index=IndexEnum.LEGACY_ORDERS)

    if index is None:
        logger.info("importing legacy orders")

        with open("/app/rarible_marketplace_indexer/jobs/data/legacy_orders.json") as source_file:
            orders = json.load(source_file)
            # chunk the work into batches of 4 lines at a time
            for order in orders:
                await import_legacy_order(order)
            await IndexingStatus.create(index=IndexEnum.LEGACY_ORDERS, last_level="SYNCED")

