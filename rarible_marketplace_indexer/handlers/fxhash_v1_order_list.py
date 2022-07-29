from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_action import FxhashListingV1OrderListEvent
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.offer import OfferParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.storage import FxhashMarketV1Storage

async def fxhash_v1_order_list(
    ctx: HandlerContext,
    offer: Transaction[OfferParameter, FxhashMarketV1Storage],
) -> None:
    await FxhashListingV1OrderListEvent.handle(offer, ctx.datasource)
