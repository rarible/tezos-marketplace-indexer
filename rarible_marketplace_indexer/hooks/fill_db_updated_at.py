import logging

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.models import TokenTransfer, Activity

logger = logging.getLogger("dipdup.fill_db_updated_at")


async def fill_db_updated_at(ctx: HookContext, batch: int):
    logger.info(f'Starting fill updated_at with batch={batch}...')
    conn = Tortoise.get_connection("default")

    items = await TokenTransfer.filter(db_updated_at=None).order_by('date').limit(int(batch))
    has_transfers = len(items) > 0
    if has_transfers:
        ids = list(set(list(map(lambda item: item.id, items))))
        await conn.execute_query(f'update token_transfer set db_updated_at=now() where id = any($1)', [ids])
        logger.info(f"Saved {len(items)} token_transfers")

    items = await Activity.filter(db_updated_at=None).order_by('operation_timestamp').limit(int(batch))
    has_order_activities = len(items) > 0
    if has_order_activities:
        ids = list(set(list(map(lambda item: item.id, items))))
        await conn.execute_query(f'update marketplace_activity set db_updated_at=now() where id = any($1)', [ids])
        logger.info(f"Saved {len(items)} marketplace_activities")
