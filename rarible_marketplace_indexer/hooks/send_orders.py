import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import Tasks, Order
from rarible_marketplace_indexer.producer.container import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.order.factory import RaribleApiOrderFactory

logger = logging.getLogger("dipdup.send_orders")


async def send_orders(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        platform = task.param
        request = Order.filter(platform=platform, id__lt=id, status='ACTIVE') if task.sample is not None else Order.filter(platform=platform, status='ACTIVE')
        orders = await request.order_by('-id').limit(1000)
        if len(orders) > 0:
            for order in orders:
                event = RaribleApiOrderFactory.build(order)
                await producer_send(event)
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
