import logging
import traceback
import uuid

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.order.order_reduce import order_full_reduce
from rarible_marketplace_indexer.models import Tasks, Order

logger = logging.getLogger("dipdup.fix_null_make")


async def fix_null_make(ctx: HookContext, id: int) -> None:
    conn = Tortoise.get_connection("default")
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        request = Order.filter(make_value__lte=0)
        orders = await request.limit(10000)
        if len(orders) > 0:
            for order in orders:
                await order_full_reduce(order, conn)
            logger.info(f"Task={task.name} sent {len(orders)} orders, set sample={task.sample}")
        else:
            logger.info(f"Task={task.name} finished")
            task.status = TaskStatus.FINISHED
    except Exception as err:
        txt = traceback.format_exc()
        task.error = txt
        task.status = TaskStatus.FAILED
        logger.error(f"Task={task.name} failed with {err}")
        logger.error(f"Task={task.name} trace: {txt}")
    task.version += 1
    await task.save()


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return val
    except ValueError:
        return None
