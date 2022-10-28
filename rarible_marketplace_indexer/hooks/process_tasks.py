import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import TokenTransfer, Tasks

logger = logging.getLogger("process_tasks")


async def process_tasks(ctx: HookContext):
    logger.info(f'Looking for new tasks...')
    tasks = await Tasks.filter(status)

