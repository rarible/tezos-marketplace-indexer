import logging
import traceback
from datetime import datetime, timedelta

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks, Ownership, TokenTransfer

logger = logging.getLogger("dipdup.remove_reverted_transfers")


async def remove_reverted_transfers(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        days = int(task.param)
        d = datetime.today() - timedelta(days=days)
        transfers = await TokenTransfer.filter(
            hash=None, tzkt_transaction_id__isnull=False, tzkt_origination_id=None, date__lt=d
        ).limit(1000)
        logger.info(f"Deleting transfers without hash (reverted) before {d}")
        for transfer in transfers:
            contract = transfer.contract
            token_id = transfer.token_id
            to_address = transfer.to_address
            from_address = transfer.from_address
            date = transfer.date
            await transfer.delete()
            await update_ownership(contract, token_id, to_address, date)
            await update_ownership(contract, token_id, from_address, date)
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

async def update_ownership(contract, token_id, owner, date):
    null_addresses = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]
    if owner not in null_addresses:
        logger.info(f"Updating ownership: {contract}:{token_id}:{owner}")
        await process(contract, token_id, owner, date)
