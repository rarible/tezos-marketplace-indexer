import logging
import traceback
from datetime import datetime

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import OrderStatusEnum
from rarible_marketplace_indexer.models import Order

logger = logging.getLogger("dipdup.start_end")


async def start_end(ctx: HookContext, batch):
    logger.info(f'Starting start_end checker with batch={batch}')

    # There are no orders with start > now
    orders = await Order.filter(
        status=OrderStatusEnum.ACTIVE,
        end_at__lt=datetime.now()).limit(int(batch))
    if len(orders) > 0:
        logger.info(f'Found {len(orders)} expired orders')
        try:
            for order in orders:
                order.status = OrderStatusEnum.INACTIVE
                order.ended_at = datetime.now()
                order.save()
        except Exception as ex:
            trace = traceback.format_exc()
            logger.error(f'Error during getting changing status for order={order.id}, {ex}, {trace}')
