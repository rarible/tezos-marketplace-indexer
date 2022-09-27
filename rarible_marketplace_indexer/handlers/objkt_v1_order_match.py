
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.event.objkt_action import ObjktV1OrderMatchEvent
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.fulfill_ask import FulfillAskParameter
from dipdup.models import Transaction

async def objkt_v1_order_match(
    ctx: HandlerContext,
    fulfill_ask: Transaction[FulfillAskParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1OrderMatchEvent.handle(fulfill_ask, ctx.datasource)
