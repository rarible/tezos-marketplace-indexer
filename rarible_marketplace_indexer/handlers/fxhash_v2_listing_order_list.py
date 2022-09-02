from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2ListingOrderListEvent
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing import ListingParameter
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage


async def fxhash_v2_listing_order_list(
    ctx: HandlerContext,
    listing: Transaction[ListingParameter, FxhashV2Storage],
) -> None:
    await FxhashV2ListingOrderListEvent.handle(listing, ctx.datasource)
