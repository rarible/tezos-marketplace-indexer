from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.versum_v1_action import VersumV1PutBidEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.make_offer import MakeOfferParameter
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage


async def versum_v1_put_bid(
    ctx: HandlerContext,
    make_offer: Transaction[MakeOfferParameter, VersumV1Storage],
) -> None:
    await VersumV1PutBidEvent.handle(make_offer, ctx.datasource)
