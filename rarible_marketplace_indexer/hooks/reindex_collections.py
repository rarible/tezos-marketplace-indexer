import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.hooks.process_collection_events import process_originations
from rarible_marketplace_indexer.models import Tasks

logger = logging.getLogger("dipdup.reindex_collections")


async def reindex_collections(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    batch = int(ctx.config.hooks.get('reindex_collections').args.get("batch"))
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        current_level = int(task.sample or task.param)
        last_id = 0
        total = 0
        for step in range(batch):
            current_level, last_id, total = await process_originations(ctx, current_level, last_id)
            if total < 100:
                break
        if total > 0:
            task.sample = current_level
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
