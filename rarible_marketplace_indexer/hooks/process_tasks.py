import logging

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Tasks

logger = logging.getLogger("dipdup.process_tasks")


async def process_tasks(ctx: HookContext):
    logger.debug('Looking for new or running tasks...')
    tasks = await Tasks.filter(status__in=['NEW', 'RUNNING'])
    for task in tasks:
        logger.info(f"Starting task={task.name} with param={task.param}")
        await ctx.fire_hook(task.name, wait=False, id=task.id)
