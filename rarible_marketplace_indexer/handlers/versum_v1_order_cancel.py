from rarible_marketplace_indexer.event.versum_v1_action import VersumV1OrderCancelEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.cancel_swap import CancelSwapParameter
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage
from dipdup.context import HandlerContext
from dipdup.models import Transaction

async def versum_v1_order_cancel(
    ctx: HandlerContext,
    cancel_swap: Transaction[CancelSwapParameter, VersumV1Storage],
) -> None:
    await VersumV1OrderCancelEvent.handle(cancel_swap, ctx.datasource)
