from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_action import FxhashListingV1OrderMatchEvent
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.collect import CollectParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.storage import FxhashMarketV1Storage

async def fxhash_v1_order_match(
    ctx: HandlerContext,
    collect: Transaction[CollectParameter, FxhashMarketV1Storage],
) -> None:
    await FxhashListingV1OrderMatchEvent.handle(collect, ctx.datasource)
