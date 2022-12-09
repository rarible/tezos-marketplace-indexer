import json
import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks, Ownership

logger = logging.getLogger("dipdup.recalculate_ownerships_by_owner")


async def recalculate_ownerships_by_owner(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        param = json.loads(task.param)
        owner = param['owner']
        ownerships = await Ownership.filter(owner=owner)
        for ownership in ownerships:
            logger.info(f"Updating ownership: {ownership.full_id()}")
            await process(ownership.contract, ownership.token_id, ownership.owner, ownership.updated)
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
