import logging
import traceback
import uuid

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.order.order_reduce import order_full_reduce
from rarible_marketplace_indexer.models import Tasks, Order

logger = logging.getLogger("dipdup.recalculate_order_make")


async def recalculate_orders(ctx: HookContext, id: int) -> None:
    conn = Tortoise.get_connection("default")
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        platform = task.param
        continuation = task.sample
        continuation = is_valid_uuid(continuation)
        if platform is None:
            request = Order.filter(id__lt=continuation) if continuation is not None else Order.filter()
        else:
            request = Order.filter(platform=platform, id__lt=continuation) if continuation is not None else Order.filter(platform=platform)
        orders = await request.order_by('-id').limit(2000)
        if len(orders) > 0:
            for order in orders:
                await order_full_reduce(order, conn)
            task.sample = orders[-1].id
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
