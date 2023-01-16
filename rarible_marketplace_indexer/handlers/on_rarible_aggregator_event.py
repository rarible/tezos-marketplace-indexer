from dipdup.context import HandlerContext
from dipdup.models import Event

from rarible_marketplace_indexer.models import AggregatorEvent
from rarible_marketplace_indexer.types.rarible_aggregator_tracker.event.aggregator_event import AggregatorEventPayload


async def on_rarible_aggregator_event(
    ctx: HandlerContext,
    event: Event[AggregatorEventPayload],
) -> None:
    tx_operation_hash = await ctx.datasource.request(
        method='get', url='v1/operations/transactions?select=hash&id=' + str(event.data.transaction_id)
    )
    stored_event = await AggregatorEvent.get_or_none(id=event.data.id)
    if stored_event is None:
        await AggregatorEvent.create(
            id=event.data.id,
            tracker=event.payload.__root__,
            level=event.data.level,
            operation_hash=tx_operation_hash[0],
        )
