from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2CancelBidEvent
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer_cancel import OfferCancelParameter
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage


async def fxhash_v2_cancel_bid(
    ctx: HandlerContext,
    offer_cancel: Transaction[OfferCancelParameter, FxhashV2Storage],
) -> None:
    await FxhashV2CancelBidEvent.handle(offer_cancel, ctx.datasource)
