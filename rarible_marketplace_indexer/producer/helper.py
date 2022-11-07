from rarible_marketplace_indexer.producer.container import ProducerContainer
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.utils.rarible_utils import get_kafka_key


async def producer_send(api_object: AbstractRaribleApiObject):
    producer = ProducerContainer.get_instance()
    await producer.send(topic=api_object.kafka_topic, key=get_kafka_key(api_object), value=api_object)

