import uuid
from dataclasses import dataclass
from typing import List, Optional

from humps.main import camelize

from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import (
    AbstractRaribleApiObject,
)
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import (
    ImplicitAccountAddress,
    OriginatedAccountAddress,
)


@dataclass
class Collection:
    id: OriginatedAccountAddress
    owner: Optional[ImplicitAccountAddress]
    name: Optional[str]
    minters: List[ImplicitAccountAddress]
    standard: str = "fa2"
    symbol: Optional[str] = None


class RaribleApiCollection(AbstractRaribleApiObject):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True

    _kafka_topic = KafkaTopic.COLLECTION_TOPIC

    id: uuid.UUID
    network: str
    event_id: str
    collection: Collection
    type: str = "UPDATE"

    def get_key(self):
        return f"{self.collection.id}"
