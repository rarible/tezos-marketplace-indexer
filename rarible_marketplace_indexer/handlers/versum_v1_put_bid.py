
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.event.versum_v1_action import VersumV1AcceptBidEvent
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.versum_v1.parameter.make_offer import MakeOfferParameter

async def versum_v1_put_bid(
    ctx: HandlerContext,
    make_offer: Transaction[MakeOfferParameter, VersumV1Storage],
) -> None:
    await VersumV1AcceptBidEvent.handle(make_offer, ctx.datasource)