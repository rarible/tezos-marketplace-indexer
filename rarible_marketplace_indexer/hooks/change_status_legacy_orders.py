import logging

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import OrderStatusEnum
from rarible_marketplace_indexer.models import Order

logger = logging.getLogger("dipdup.change_status_legacy_orders")


async def change_status_legacy_orders(ctx: HookContext, batch):
    logger.info(f'Starting change_status_legacy_orders')
    conn = Tortoise.get_connection("default")
    result = await conn.execute_query("""
        select l.id from marketplace_order l
        join lateral (select * from marketplace_order where make_contract = l.make_contract and make_token_id = l.make_token_id and platform <> l.platform and last_updated_at > l.last_updated_at limit 1) o on true
        where l.status = 'ACTIVE' and l.platform = 'RARIBLE_V1'
        limit $1
    """, [int(batch)])
    if result[0] > 0:
        logger.info(f'Found {result[0]} outdated orders')
        for row in result[1]:
            if row['id'] is not None:
                order = await Order.get(id=row['id'])
                order.status = OrderStatusEnum.CANCELLED
                order.cancelled = True
                logger.info(f'Change status for {order.id} order')
                await order.save()
    else:
        logger.info(f'No outdated orders were found')
