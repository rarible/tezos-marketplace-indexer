from dipdup.context import HandlerContext
from dipdup.models import Event

from rarible_marketplace_indexer.models import AggregatorEvent
from rarible_marketplace_indexer.types.rarible_aggregator_tracker.event.aggregator_event import AggregatorEventPayload


async def on_rarible_aggregator_event(
    ctx: HandlerContext,
    event: Event[AggregatorEventPayload],
) -> None:
    tzkt_event_data = await ctx.get_tzkt_datasource('tzkt').request(
        method='get', url='/v1/contracts/events?id=' + str(event.data.id)
    )
    tx_id = tzkt_event_data[0].get("transactionId")
    tx_operation_hash = await ctx.get_tzkt_datasource('tzkt').request(
        method='get', url='/v1/operations/transactions?select=hash&id=' + str(tx_id)
    )
    stored_event = await AggregatorEvent.get_or_none(id=event.data.id)
    if stored_event is None:
        await AggregatorEvent.create(
            id=event.data.id,
            tracker=event.payload.__root__,
            level=event.data.level,
            operation_hash=tx_operation_hash[0],
        )
