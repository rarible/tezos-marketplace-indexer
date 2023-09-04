import logging

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import TokenTransfer, Activity, Tasks

logger = logging.getLogger("dipdup.fix_db_updated_at")


async def fix_db_updated_at(ctx: HookContext, id: int):
    batch = ctx.config.hooks.get('fix_db_updated_at').args.get("batch")
    task = await Tasks.get_or_none(id=id)
    conn = Tortoise.get_connection("default")
    try:
        task.status = TaskStatus.RUNNING
        tt = await TokenTransfer.filter(db_updated_at__lt=task.created).limit(int(batch))
        sum = 0
        has_transfers = len(tt) > 0
        if has_transfers:
            ids = list(set(list(map(lambda item: item.id, tt))))
            await conn.execute_query("update token_transfer set db_updated_at=date_trunc('second', now()::timestamp) where id = any($1)", [ids])
            logger.info(f"Fixed {len(tt)} token_transfers")
            sum += len(tt)

        ma = await Activity.filter(db_updated_at__lt=task.created).limit(int(batch))
        has_order_activities = len(ma) > 0
        if has_order_activities:
            ids = list(set(list(map(lambda item: item.id, ma))))
            await conn.execute_query("update marketplace_activity set db_updated_at=date_trunc('second', now()::timestamp) where id = any($1)", [ids])
            logger.info(f"Fixed {len(ma)} marketplace_activities")
            sum += len(ma)

        if sum > 0:
            prev = task.sample
            if prev is None:
                task.sample = sum
            else:
                task.sample = int(prev) + sum
            logger.info(f"Task={task.name} updated, fixed {task.sample} items: {len(tt)} token_transfers, {len(ma)} marketplace activities")
        else:
            logger.info(f"Task={task.name} finished")
            task.status = TaskStatus.FINISHED
    except Exception as err:
        task.error = str
        task.status = TaskStatus.FAILED
        logger.error(f"Task={task.name} failed with {err}")
        logger.error(f"Task={task.name} trace: {str}")
    task.version += 1
    await task.save()
