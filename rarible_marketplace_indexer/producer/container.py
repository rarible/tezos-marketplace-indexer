from __future__ import annotations

import logging
import time
from logging import Logger
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from aiokafka import AIOKafkaProducer

from rarible_marketplace_indexer.producer.helper import get_kafka_key
from rarible_marketplace_indexer.producer.null_kafka_producer import NullKafkaProducer
from rarible_marketplace_indexer.producer.serializer import kafka_key_serializer
from rarible_marketplace_indexer.producer.serializer import kafka_value_serializer
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject

AIOKafkaProducerInterface = Union[AIOKafkaProducer, NullKafkaProducer]

logger = logging.getLogger('dipdup.kafka')

class ProducerContainer:
    __instance: Optional[AIOKafkaProducerInterface] = None

    @classmethod
    def get_instance(cls) -> AIOKafkaProducerInterface:
        if not isinstance(cls.__instance, AIOKafkaProducerInterface):
            raise RuntimeError
        return cls.__instance

    @classmethod
    def create_instance(cls, config: Dict[str, Any], logger: Logger) -> None:
        if config['enabled'] != 'false':
            addresses = config['kafka_address'].split(',')
            logger.info(f"Connecting to internal kafka: {addresses}")
            producer = AIOKafkaProducer(
                bootstrap_servers=addresses,
                client_id=config['client_id'],
                sasl_mechanism=config['sasl']['mechanism'],
                value_serializer=kafka_value_serializer,
                key_serializer=kafka_key_serializer,
            )
        else:
            producer = NullKafkaProducer()

        cls.__instance = producer


async def producer_send(api_object: AbstractRaribleApiObject):
    producer = ProducerContainer.get_instance()
    await producer.send(topic=api_object.kafka_topic, key=get_kafka_key(api_object), value=api_object)
