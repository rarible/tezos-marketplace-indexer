import json
import logging
import traceback

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks, TokenTransfer, Royalties

logger = logging.getLogger("dipdup.reset_royalty_flag")


async def reset_royalty_flag(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()

        conn = Tortoise.get_connection("default")
        await conn.execute_query(
        """
        update royalties set royalties_synced = false where royalties_synced = true and parts @> '[{"part_value":"0"}]'
        """)

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
