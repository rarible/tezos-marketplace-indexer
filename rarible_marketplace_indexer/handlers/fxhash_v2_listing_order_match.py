from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2ListingOrderMatchEvent
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing_accept import ListingAcceptParameter
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage


async def fxhash_v2_listing_order_match(
    ctx: HandlerContext,
    listing_accept: Transaction[ListingAcceptParameter, FxhashV2Storage],
) -> None:
    await FxhashV2ListingOrderMatchEvent.handle(listing_accept, ctx.datasource)
