from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_action import FxhashListingV1OrderCancelEvent
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.cancel_offer import CancelOfferParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.storage import FxhashMarketV1Storage

async def fxhash_v1_order_cancel(
    ctx: HandlerContext,
    cancel_offer: Transaction[CancelOfferParameter, FxhashMarketV1Storage],
) -> None:
    await FxhashListingV1OrderCancelEvent.handle(cancel_offer, ctx.datasource)
