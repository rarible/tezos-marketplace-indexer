
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.event.objkt_action import ObjktV1OrderListEvent
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.ask import AskParameter

async def objkt_v1_order_list(
    ctx: HandlerContext,
    ask: Transaction[AskParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1OrderListEvent.handle(ask, ctx.datasource)
