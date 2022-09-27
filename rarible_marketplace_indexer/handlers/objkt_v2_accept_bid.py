
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.fulfill_offer import FulfillOfferParameter
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.types.objkt_marketplace_v2.storage import ObjktMarketplaceV2Storage
from dipdup.models import Transaction

async def objkt_v2_accept_bid(
    ctx: HandlerContext,
    fulfill_offer: Transaction[FulfillOfferParameter, ObjktMarketplaceV2Storage],
) -> None:
    ...