import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks, Ownership

logger = logging.getLogger("dipdup.recalculate_ownerships")


async def recalculate_ownerships(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    batch = int(ctx.config.hooks.get('recalculate_ownerships').args.get("batch"))
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        request = Ownership.filter(id__lt=task.sample) if task.sample is not None else Ownership.all()
        ownerships = await request.order_by('-id').limit(batch)
        if len(ownerships) > 0:
            for ownership in ownerships:
                await process(ownership.contract, ownership.token_id, ownership.owner, ownership.updated)
            task.sample = ownerships[-1].id
            logger.info(f"Task={task.name} updated {len(ownerships)} ownerships, set sample={task.sample}")
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
