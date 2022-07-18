from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.rarible_action import RaribleLegacyOrderMatchEvent
from rarible_marketplace_indexer.types.rarible_exchange_legacy.parameter.match_orders import MatchOrdersParameter
from rarible_marketplace_indexer.types.rarible_exchange_legacy.storage import RaribleExchangeLegacyStorage


async def rarible_match_order_legacy(
    ctx: HandlerContext,
    match_orders: Transaction[MatchOrdersParameter, RaribleExchangeLegacyStorage],
) -> None:
    await RaribleLegacyOrderMatchEvent.handle(match_orders, ctx.datasource)
