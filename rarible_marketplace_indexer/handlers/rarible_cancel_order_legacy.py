
from dipdup.context import HandlerContext

from rarible_marketplace_indexer.event.rarible_action import RaribleLegacyOrderCancelEvent
from rarible_marketplace_indexer.types.rarible_exchange_legacy.storage import RaribleExchangeLegacyStorage
from rarible_marketplace_indexer.types.rarible_exchange_legacy.parameter.cancel import CancelParameter
from dipdup.models import Transaction

async def rarible_cancel_order_legacy(
    ctx: HandlerContext,
    cancel: Transaction[CancelParameter, RaribleExchangeLegacyStorage],
) -> None:
    await RaribleLegacyOrderCancelEvent.handle(cancel, ctx.datasource)
