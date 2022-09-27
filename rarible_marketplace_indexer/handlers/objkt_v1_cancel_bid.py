
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.event.objkt_action import ObjktV1CancelBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.retract_bid import RetractBidParameter

async def objkt_v1_cancel_bid(
    ctx: HandlerContext,
    retract_bid: Transaction[RetractBidParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1CancelBidEvent.handle(retract_bid, ctx.datasource)
