from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.objkt_action import ObjktV1AcceptBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.fulfill_bid import FulfillBidParameter
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage


async def objkt_v1_accept_bid(
    ctx: HandlerContext,
    fulfill_bid: Transaction[FulfillBidParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1AcceptBidEvent.handle(fulfill_bid, ctx.datasource)
