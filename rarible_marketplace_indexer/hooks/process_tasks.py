import logging

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Tasks

logger = logging.getLogger("dipdup.process_tasks")


async def process_tasks(ctx: HookContext):
    logger.debug('Looking for new or running tasks...')
    tasks = await Tasks.filter(status__in=['NEW', 'RUNNING'])
    for task in tasks:
        if task.status == 'NEW' and task.sample is None:
            logger.info(f"Starting task={task.name} with param={task.param}")
            await ctx.fire_hook(task.name, wait=False, id=task.id)
        elif task.status == 'RUNNING' and task.sample is not None:
            logger.info(f"Continuing task={task.name} with param={task.param} and sample={task.sample}")
            await ctx.fire_hook(task.name, wait=False, id=task.id)
