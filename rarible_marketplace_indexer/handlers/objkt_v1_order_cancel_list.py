from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.objkt_action import ObjktV1OrderCancelEvent
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.retract_ask import RetractAskParameter
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage


async def objkt_v1_order_cancel_list(
    ctx: HandlerContext,
    retract_ask: Transaction[RetractAskParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1OrderCancelEvent.handle(retract_ask, ctx.datasource)
