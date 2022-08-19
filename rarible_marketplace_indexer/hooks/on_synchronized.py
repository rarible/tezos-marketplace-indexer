import asyncio

from dipdup.context import HookContext

from rarible_marketplace_indexer.jobs.legacy_data import cancel_obsolete_v1_orders, fix_v1_fill_value


async def on_synchronized(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql('on_synchronized')
    asyncio.ensure_future(cancel_obsolete_v1_orders())
    asyncio.ensure_future(fix_v1_fill_value())

