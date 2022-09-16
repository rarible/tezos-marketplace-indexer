import asyncio
import os

from dipdup.context import HookContext

from rarible_marketplace_indexer.jobs.legacy_data import cancel_obsolete_v1_orders
from rarible_marketplace_indexer.jobs.legacy_data import fix_v1_fill_value


async def on_synchronized(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql('on_synchronized')
    if os.getenv('APPLICATION_ENVIRONMENT') == 'prod' and ctx.config.custom.get("run_fix_jobs") is not None:
        if ctx.config.custom.get("run_fix_jobs") is True:
            asyncio.ensure_future(cancel_obsolete_v1_orders())
            asyncio.ensure_future(fix_v1_fill_value())
