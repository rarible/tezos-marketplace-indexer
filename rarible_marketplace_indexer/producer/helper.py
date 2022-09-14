from typing import List

from tortoise.signals import post_save

from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import OrderModel
from rarible_marketplace_indexer.producer.container import ProducerContainer
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.utils.rarible_utils import get_kafka_key


async def producer_send(api_object: AbstractRaribleApiObject):
    producer = ProducerContainer.get_instance()
    await producer.send(topic=api_object.kafka_topic, key=get_kafka_key(api_object), value=api_object)


@post_save(OrderModel)
async def signal_order_post_save(
    sender: OrderModel,
    instance: OrderModel,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.order.factory import RaribleApiOrderFactory

    await producer_send(RaribleApiOrderFactory.build(instance))


@post_save(ActivityModel)
async def signal_activity_post_save(
    sender: ActivityModel,
    instance: ActivityModel,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.factory import (
        RaribleApiOrderActivityFactory,
    )

    await producer_send(RaribleApiOrderActivityFactory.build(instance))
