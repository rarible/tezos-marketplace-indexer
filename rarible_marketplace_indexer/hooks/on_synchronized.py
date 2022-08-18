import asyncio

from dipdup.context import HookContext

from rarible_marketplace_indexer.jobs.legacy_data import clean_v1_data


async def on_synchronized(
    ctx: HookContext,
) -> None:
    await ctx.execute_sql('on_synchronized')
    asyncio.ensure_future(clean_v1_data())

