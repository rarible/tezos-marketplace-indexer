import json
import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import Tasks, Royalties

logger = logging.getLogger("dipdup.reset_royalty_by_contract")


async def reset_royalty_by_id(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        royalties = await Royalties.filter(contract=task.param)
        for royalty in royalties:
            logger.info(f"Resetting royalty: {royalty.contract}:{royalty.token_id}")
            royalty.royalties_synced = False
            await royalty.save()
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
