from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2AcceptBidEvent
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer_accept import OfferAcceptParameter
from dipdup.models import Transaction

async def fxhash_v2_accept_bid(
    ctx: HandlerContext,
    offer_accept: Transaction[OfferAcceptParameter, FxhashV2Storage],
) -> None:
    await FxhashV2AcceptBidEvent.handle(offer_accept, ctx.datasource)
