import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from humps.main import camelize

from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


@dataclass
class OwnershipBody:
    id: Optional[str]
    contract: OriginatedAccountAddress
    token_id: str
    owner: ImplicitAccountAddress
    value: AssetValue
    date: datetime


class RaribleApiOwnership(AbstractRaribleApiObject):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True

    _kafka_topic = KafkaTopic.OWNERSHIP_TOPIC

    event_id: uuid.UUID
    ownership_id: str
    ownership: Optional[OwnershipBody]
    type: str
