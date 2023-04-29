import logging
import traceback
import uuid

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import Tasks, Ownership, Order

logger = logging.getLogger("dipdup.recalculate_order_make")


async def recalculate_order_make(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        platform = task.param
        continuation = task.sample
        continuation = is_valid_uuid(continuation)
        request = Order.filter(platform=platform, id__lt=continuation, status='ACTIVE') if continuation is not None else Order.filter(platform=platform, status='ACTIVE')
        orders = await request.order_by('-id').limit(1000)
        if len(orders) > 0:
            for order in orders:
                old_make = order.make_value
                ownership_id = Ownership.get_id(order.make_contract, order.make_token_id, order.maker)
                ownership = await Ownership.get_or_none(id=ownership_id)
                if ownership is None:
                    order.make_value = 0
                else:
                    order.make_value = min(ownership.balance, order.make_value)
                if order.make_value == 0:
                    order.status = 'INACTIVE'
                if old_make != order.make_value:
                    logger.info(f"Order changed id={order.id} ({order.platform}): make_value={old_make}->{order.make_value}, status={order.status}")
                    await order.save()
            task.sample = orders[-1].id
            logger.info(f"Task={task.name} sent {len(orders)} {platform} orders, set sample={task.sample}")
        else:
            logger.info(f"Task={task.name} finished")
            task.status = TaskStatus.FINISHED
    except Exception as err:
        str = traceback.format_exc()
        task.error = str
        task.status = TaskStatus.FAILED
        logger.error(f"Task={task.name} failed with {err}")
        logger.error(f"Task={task.name} trace: {str}")
    task.version += 1
    await task.save()
def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return val
    except ValueError:
        return None
