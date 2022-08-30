from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.versum_v1_action import VersumV1OrderListEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.create_swap import CreateSwapParameter
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage


async def versum_v1_order_list(
    ctx: HandlerContext,
    create_swap: Transaction[CreateSwapParameter, VersumV1Storage],
) -> None:
    await VersumV1OrderListEvent.handle(create_swap, ctx.datasource)
