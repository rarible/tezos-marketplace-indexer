from datetime import datetime
from typing import List
from typing import Optional

from humps.main import camelize

from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import AbstractAsset
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress


class RaribleApiOrder(AbstractRaribleApiObject):
    class Config:
        alias_generator = camelize
        allow_population_by_field_name = True
        use_enum_values = True

    _kafka_topic = KafkaTopic.ORDER_TOPIC
    fill: Xtz
    internal_order_id: str
    network: str
    platform: PlatformEnum
    status: OrderStatusEnum
    start_at: datetime
    end_at: Optional[datetime]
    cancelled: bool
    created_at: datetime
    ended_at: Optional[datetime]
    last_updated_at: datetime
    maker: ImplicitAccountAddress
    taker: Optional[ImplicitAccountAddress]
    make: AbstractAsset
    take: Optional[AbstractAsset]
    make_price: Optional[AssetValue]
    take_price: Optional[AssetValue]
    origin_fees: List[Part]
    payouts: List[Part]
    salt: int
