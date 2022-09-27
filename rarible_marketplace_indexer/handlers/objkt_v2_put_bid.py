
from rarible_marketplace_indexer.types.objkt_marketplace_v2.storage import ObjktMarketplaceV2Storage
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.offer import OfferParameter

async def objkt_v2_put_bid(
    ctx: HandlerContext,
    offer: Transaction[OfferParameter, ObjktMarketplaceV2Storage],
) -> None:
    ...