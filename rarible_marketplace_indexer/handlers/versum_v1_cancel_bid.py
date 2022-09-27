
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.event.versum_v1_action import VersumV1CancelBidEvent
from rarible_marketplace_indexer.types.versum_v1.parameter.cancel_offer import CancelOfferParameter
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage

async def versum_v1_cancel_bid(
    ctx: HandlerContext,
    cancel_offer: Transaction[CancelOfferParameter, VersumV1Storage],
) -> None:
    await VersumV1CancelBidEvent.handle(cancel_offer, ctx.datasource)