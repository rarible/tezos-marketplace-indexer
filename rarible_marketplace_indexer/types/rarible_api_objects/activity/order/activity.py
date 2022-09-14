import uuid
from datetime import datetime
from typing import Literal, Optional, Union

from rarible_marketplace_indexer.models import ActivityTypeEnum, PlatformEnum
from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import (
    AbstractRaribleApiObject,
)
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import (
    AbstractAsset,
    TokenAsset,
)
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import (
    ImplicitAccountAddress,
    OperationHash,
)


class AbstractRaribleApiOrderActivity(AbstractRaribleApiObject):
    _kafka_topic = KafkaTopic.ACTIVITY_TOPIC
    type: str
    order_id: uuid.UUID
    source: PlatformEnum
    hash: OperationHash
    date: datetime
    reverted: bool = False


class RaribleApiOrderListActivity(AbstractRaribleApiOrderActivity):
    type: Literal[
        ActivityTypeEnum.ORDER_LIST,
        ActivityTypeEnum.MAKE_BID,
        ActivityTypeEnum.MAKE_FLOOR_BID,
    ] = ActivityTypeEnum.ORDER_LIST
    maker: ImplicitAccountAddress
    make: AbstractAsset
    take: Optional[AbstractAsset]

    def get_key(self):
        if self.make is TokenAsset:
            make: TokenAsset = self.make
            return f"{make.asset_type.contract}:{make.asset_type.token_id}"
        elif self.take is TokenAsset:
            take: TokenAsset = self.take
            return f"{take.asset_type.contract}:{take.asset_type.token_id}"
        else:
            return self.order_id


class RaribleApiOrderMatchActivity(AbstractRaribleApiOrderActivity):
    type: Literal[
        ActivityTypeEnum.ORDER_MATCH,
        ActivityTypeEnum.GET_BID,
        ActivityTypeEnum.GET_FLOOR_BID,
    ] = ActivityTypeEnum.ORDER_MATCH
    nft: AbstractAsset
    payment: Optional[AbstractAsset]
    buyer: ImplicitAccountAddress
    seller: ImplicitAccountAddress

    def get_key(self):
        if self.nft is TokenAsset:
            make: TokenAsset = self.nft
            return f"{make.asset_type.contract}:{make.asset_type.token_id}"
        elif self.payment is TokenAsset:
            take: TokenAsset = self.payment
            return f"{take.asset_type.contract}:{take.asset_type.token_id}"
        else:
            return self.order_id


class RaribleApiOrderCancelActivity(AbstractRaribleApiOrderActivity):
    type: Literal[
        ActivityTypeEnum.ORDER_CANCEL,
        ActivityTypeEnum.CANCEL_BID,
        ActivityTypeEnum.CANCEL_FLOOR_BID,
    ] = ActivityTypeEnum.ORDER_CANCEL
    maker: ImplicitAccountAddress
    make: AbstractAsset
    take: Optional[AbstractAsset]

    def get_key(self):
        if self.make is TokenAsset:
            make: TokenAsset = self.make
            return f"{make.asset_type.contract}:{make.asset_type.token_id}"
        elif self.take is TokenAsset:
            take: TokenAsset = self.take
            return f"{take.asset_type.contract}:{take.asset_type.token_id}"
        else:
            return self.order_id


RaribleApiOrderActivity = Union[
    RaribleApiOrderListActivity,
    RaribleApiOrderMatchActivity,
    RaribleApiOrderCancelActivity,
]
