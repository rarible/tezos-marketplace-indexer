from rarible_marketplace_indexer.event.teia_v1_action import TeiaV1OrderListEvent
from rarible_marketplace_indexer.types.teia_v1.parameter.swap import SwapParameter
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.teia_v1.storage import TeiaV1Storage

async def teia_v1_list_order(
    ctx: HandlerContext,
    swap: Transaction[SwapParameter, TeiaV1Storage],
) -> None:
    await TeiaV1OrderListEvent.handle(swap, ctx.datasource)
