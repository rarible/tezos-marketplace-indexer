from rarible_marketplace_indexer.event.objkt_action import ObjktV1PutBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.bid import BidParameter
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from dipdup.models import Transaction

async def objkt_v1_put_bid(
    ctx: HandlerContext,
    bid: Transaction[BidParameter, ObjktMarketplaceStorage],
) -> None:
    await ObjktV1PutBidEvent.handle(bid, ctx.datasource)
