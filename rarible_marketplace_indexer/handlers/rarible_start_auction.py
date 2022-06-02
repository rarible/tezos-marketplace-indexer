
from rarible_marketplace_indexer.types.rarible_auctions.storage import RaribleAuctionsStorage
from dipdup.context import HandlerContext
from dipdup.models import Transaction
from rarible_marketplace_indexer.types.rarible_auctions.parameter.start_auction import StartAuctionParameter

async def rarible_start_auction(
    ctx: HandlerContext,
    start_auction: Transaction[StartAuctionParameter, RaribleAuctionsStorage],
) -> None:
    ...