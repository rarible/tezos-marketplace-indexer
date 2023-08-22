import asyncio
import logging

from rarible_marketplace_indexer.models import Ownership, Order

logger = logging.getLogger("dipdup.order_full_reduce")


async def order_full_reduce(order, conn) -> Order:
    if not order.is_bid:

        listed, filled, balance = await asyncio.gather(
            listing(conn, order),
            sold(conn, order),
            ownerships(order)
        )
        order.make_value = listed
        order.fill = filled
        order.make_stock = min(listed - filled, balance)

        if order.make_stock < 0:
            order.make_stock = 0

        if order.status == 'ACTIVE':
            if order.make_stock == 0 and listed > filled:
                order.status = 'INACTIVE'
            if order.make_stock == 0 and listed == filled:
                order.status = 'FILLED'

        await order.save()


async def listing(conn, order):
    result = await conn.execute_query(
        "select coalesce(sum(make_value), 0) from marketplace_activity where order_id = $1 and type= 'LIST'",
        [order.id])
    return result[1][0]['coalesce']


async def sold(conn, order):
    result = await conn.execute_query(
        "select coalesce(sum(make_value), 0) from marketplace_activity where order_id = $1 and type= 'SELL'",
        [order.id])
    return result[1][0]['coalesce']


async def ownerships(order):
    ownership_id = Ownership.get_id(order.make_contract, order.make_token_id, order.maker)
    ownership = await Ownership.get_or_none(id=ownership_id)
    if ownership is None:
        return 0
    else:
        return ownership.balance
