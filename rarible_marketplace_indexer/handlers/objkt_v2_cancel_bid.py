from rarible_marketplace_indexer.event.objkt_v2_action import ObjktV2CancelBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace_v2.storage import ObjktMarketplaceV2Storage
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.retract_offer import RetractOfferParameter

async def objkt_v2_cancel_bid(
    ctx: HandlerContext,
    retract_offer: Transaction[RetractOfferParameter, ObjktMarketplaceV2Storage],
) -> None:
    await ObjktV2CancelBidEvent.handle(retract_offer, ctx.datasource)
