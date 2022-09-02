from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.teia_v1_action import TeiaV1OrderCancelEvent
from rarible_marketplace_indexer.types.teia_v1.parameter.cancel_swap import CancelSwapParameter
from rarible_marketplace_indexer.types.teia_v1.storage import TeiaV1Storage


async def teia_v1_cancel_order(
    ctx: HandlerContext,
    cancel_swap: Transaction[CancelSwapParameter, TeiaV1Storage],
) -> None:
    await TeiaV1OrderCancelEvent.handle(cancel_swap, ctx.datasource)
