import os

from dipdup.context import HandlerContext
from dipdup.models import HeadBlockData


async def on_head(
        ctx: HandlerContext,
        head: HeadBlockData,
) -> None:
    await ctx.fire_hook("process_collection_events", force_reindex=False, head=head.level)
