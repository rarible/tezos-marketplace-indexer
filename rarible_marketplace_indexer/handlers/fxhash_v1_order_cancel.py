from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.fxhash_v1_action import FxhashV1OrderCancelEvent
from rarible_marketplace_indexer.types.fxhash_v1.parameter.cancel_offer import CancelOfferParameter
from rarible_marketplace_indexer.types.fxhash_v1.storage import FxhashV1Storage


async def fxhash_v1_order_cancel(
    ctx: HandlerContext,
    cancel_offer: Transaction[CancelOfferParameter, FxhashV1Storage],
) -> None:
    await FxhashV1OrderCancelEvent.handle(cancel_offer, ctx.datasource)
