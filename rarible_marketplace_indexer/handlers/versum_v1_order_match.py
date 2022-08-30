from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.versum_v1_action import VersumV1OrderMatchEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.collect_swap import CollectSwapParameter
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage


async def versum_v1_order_match(
    ctx: HandlerContext,
    collect_swap: Transaction[CollectSwapParameter, VersumV1Storage],
) -> None:
    await VersumV1OrderMatchEvent.handle(collect_swap, ctx.datasource)
