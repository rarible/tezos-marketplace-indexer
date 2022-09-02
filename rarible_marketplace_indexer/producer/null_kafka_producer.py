from __future__ import annotations

import logging
from logging import Logger
from typing import Optional
from typing import Union

from pydantic import BaseModel

from rarible_marketplace_indexer.producer.serializer import kafka_key_serializer
from rarible_marketplace_indexer.producer.serializer import kafka_value_serializer


class NullKafkaProducer:
    def __init__(self):
        self._logger: Logger = logging.getLogger('dipdup.kafka')

    async def start(self):
        pass

    async def send(self, topic: str, value: BaseModel = None, key: Optional[Union[int, str]] = None, *args, **kwargs):
        message = {'topic': topic, 'message': {'key': kafka_key_serializer(key), 'value': kafka_value_serializer(value)}}
        self._logger.info(message)
