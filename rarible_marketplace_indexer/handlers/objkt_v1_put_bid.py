from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.objkt_action import ObjktV1PutBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.bid import BidParameter
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage


async def objkt_v1_put_bid(
    ctx: HandlerContext,
    bid: Transaction[BidParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1PutBidEvent.handle(bid, ctx.datasource)
