from rarible_marketplace_indexer.event.objkt_action import ObjktV1AcceptBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.fulfill_bid import FulfillBidParameter
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from dipdup.models import Transaction

async def objkt_v1_accept_bid(
    ctx: HandlerContext,
    fulfill_bid: Transaction[FulfillBidParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1AcceptBidEvent.handle(fulfill_bid, ctx.datasource)
