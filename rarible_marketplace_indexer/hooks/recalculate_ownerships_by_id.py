import json
import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks, TokenTransfer

logger = logging.getLogger("dipdup.recalculate_ownerships_by_item")


async def recalculate_ownerships_by_item(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        param = json.loads(task.param)
        contract = param['contract']
        token_id = param['token_id']
        owner = param['owner']
        last_transfer = await TokenTransfer.filter(contract=contract, token_id=token_id, to_address=owner).order_by('-date').first()
        logger.info(f"Updating ownership: {contract}:{token_id}:{owner}")
        await process(contract, token_id, owner, last_transfer.date)
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
