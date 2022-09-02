from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2ListingOrderCancelEvent
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage
from dipdup.models import Transaction
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing_cancel import ListingCancelParameter

async def fxhash_v2_listing_order_cancel(
    ctx: HandlerContext,
    listing_cancel: Transaction[ListingCancelParameter, FxhashV2Storage],
) -> None:
    await FxhashV2ListingOrderCancelEvent.handle(listing_cancel, ctx.datasource)
