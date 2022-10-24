from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2PutBidEvent
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer import OfferParameter
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage


async def fxhash_v2_put_bid(
    ctx: HandlerContext,
    offer: Transaction[OfferParameter, FxhashV2Storage],
) -> None:
    await FxhashV2PutBidEvent.handle(offer, ctx.datasource)
