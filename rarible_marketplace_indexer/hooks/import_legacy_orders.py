import logging
import os

import requests
from dipdup.context import HookContext

from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.utils.rarible_utils import import_legacy_order


async def import_legacy_orders(
    ctx: HookContext,
) -> None:
    logger = logging.getLogger('dipdup.legacy')

    index = await IndexingStatus.get_or_none(index=IndexEnum.LEGACY_ORDERS)

    continuation = ""

    if index is not None:
        if index.last_level == "SYNCED":
            continuation = None
        else:
            continuation = index.last_level

    while continuation is not None:
        orders = requests.get(f"{os.getenv('LEGACY_API')}/v0.1/orders/all?sort=EARLIEST_FIRST&status=ACTIVE&size=1000{continuation}").json()

        continuation_param = orders.get("continuation")
        if continuation_param is not None:
            continuation = f"&continuation={continuation_param}"
        else:
            continuation = None
        logger.info(f"Next continuation: {continuation}")

        for order in orders["orders"]:
            await import_legacy_order(order)

    if continuation is None:
        continuation = "SYNCED"

    if index is None:
        await IndexingStatus.create(index=IndexEnum.LEGACY_ORDERS, last_level=continuation)
    else:
        index.last_level = continuation
        await index.save()
