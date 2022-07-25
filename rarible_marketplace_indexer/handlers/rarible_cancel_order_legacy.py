from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.rarible_action import RaribleLegacyOrderCancelEvent
from rarible_marketplace_indexer.types.rarible_exchange_legacy.storage import RaribleExchangeLegacyStorage
from rarible_marketplace_indexer.types.rarible_exchange_legacy_data.parameter.remove import RemoveParameter


async def rarible_cancel_order_legacy(
    ctx: HandlerContext,
    remove: Transaction[RemoveParameter, RaribleExchangeLegacyStorage],
) -> None:
    await RaribleLegacyOrderCancelEvent.handle(remove, ctx.datasource)
