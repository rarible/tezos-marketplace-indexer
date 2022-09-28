from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.objkt_v2_action import ObjktV2AcceptBidEvent
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.fulfill_offer import FulfillOfferParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.storage import ObjktMarketplaceV2Storage


async def objkt_v2_accept_bid(
    ctx: HandlerContext,
    fulfill_offer: Transaction[FulfillOfferParameter, ObjktMarketplaceV2Storage],
) -> None:
    await ObjktV2AcceptBidEvent.handle(fulfill_offer, ctx.datasource)
