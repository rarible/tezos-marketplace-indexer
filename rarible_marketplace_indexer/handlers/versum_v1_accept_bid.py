from rarible_marketplace_indexer.event.versum_v1_action import VersumV1PutBidEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.accept_offer import AcceptOfferParameter
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage
from dipdup.models import Transaction

async def versum_v1_accept_bid(
    ctx: HandlerContext,
    accept_offer: Transaction[AcceptOfferParameter, VersumV1Storage],
) -> None:
    await VersumV1PutBidEvent.handle(accept_offer, ctx.datasource)