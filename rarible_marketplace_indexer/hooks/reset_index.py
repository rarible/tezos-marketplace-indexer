import json
import logging
import traceback

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.models import Tasks, TaskStatus

logger = logging.getLogger("dipdup.reset_index")


async def reset_index(ctx: HookContext, id: int) -> None:
    conn = Tortoise.get_connection("default")
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        param = json.loads(task.param)
        name = param['index']
        level = int(param['level'])
        await conn.execute_query(
            "update dipdup_index set status='SYNCING', level=$1, updated_at = now()  where name=$2",
            [level, name]
        )
        logger.info(f"Index={name} was set to {level} level")
        logger.info(f"Task={task.name} finished")
        task.status = TaskStatus.FINISHED
    except Exception as err:
        str = traceback.format_exc()
        task.error = str
        task.status = TaskStatus.FAILED
        logger.error(f"Task={task.name} failed with {str}")
    await task.save()
    await ctx.restart()

