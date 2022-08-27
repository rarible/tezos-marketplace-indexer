from dipdup.context import HandlerContext
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.teia_v1_action import TeiaV1OrderMatchEvent
from rarible_marketplace_indexer.types.teia_v1.parameter.collect import CollectParameter
from rarible_marketplace_indexer.types.teia_v1.storage import TeiaV1Storage


async def teia_v1_match_order(
    ctx: HandlerContext,
    collect: Transaction[CollectParameter, TeiaV1Storage],
) -> None:
    await TeiaV1OrderMatchEvent.handle(collect, ctx.datasource)
