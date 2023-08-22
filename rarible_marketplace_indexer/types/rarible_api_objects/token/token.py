import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List
from typing import Optional

from humps.main import camelize

from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


@dataclass
class TokenBody:
    id: Optional[str]
    contract: OriginatedAccountAddress
    token_id: str
    creators: List[Part]
    supply: AssetValue
    minted: AssetValue
    minted_at: datetime
    updated: datetime
    deleted: bool


class RaribleApiToken(AbstractRaribleApiObject):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True

    _kafka_topic = KafkaTopic.ITEM_TOPIC

    event_id: uuid.UUID
    item_id: str
    item: Optional[TokenBody]
    type: str


class RaribleItemMeta(AbstractRaribleApiObject):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True

    _kafka_topic = KafkaTopic.ITEM_META_TOPIC

    item_id: str
    type: str
