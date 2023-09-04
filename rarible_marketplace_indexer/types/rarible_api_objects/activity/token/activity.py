from datetime import datetime
from typing import Any
from typing import Literal
from typing import Optional
from typing import Union

from pydantic import Field

from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.producer.const import KafkaTopic
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


class BaseRaribleApiTokenActivity(AbstractRaribleApiObject):
    _kafka_topic = KafkaTopic.ACTIVITY_TOPIC
    id: str
    transfer_id: int
    network: Optional[str]
    contract: OriginatedAccountAddress
    token_id: int
    value: AssetValue
    transaction_id: int
    reverted: bool = False
    date: datetime

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self.id = str(self.transfer_id)


class RaribleApiTokenMintActivity(BaseRaribleApiTokenActivity):
    type: Literal[ActivityTypeEnum.TOKEN_MINT] = ActivityTypeEnum.TOKEN_MINT
    owner: Union[ImplicitAccountAddress, OriginatedAccountAddress]


class RaribleApiTokenTransferActivity(BaseRaribleApiTokenActivity):
    type: Literal[ActivityTypeEnum.TOKEN_TRANSFER] = ActivityTypeEnum.TOKEN_TRANSFER
    transfer_from: Union[ImplicitAccountAddress, OriginatedAccountAddress] = Field(alias="from")
    owner: Union[ImplicitAccountAddress, OriginatedAccountAddress]


class RaribleApiTokenBurnActivity(BaseRaribleApiTokenActivity):
    type: Literal[ActivityTypeEnum.TOKEN_BURN] = ActivityTypeEnum.TOKEN_BURN
    owner: Union[ImplicitAccountAddress, OriginatedAccountAddress]


RaribleApiTokenActivity = Union[
    RaribleApiTokenMintActivity,
    RaribleApiTokenTransferActivity,
    RaribleApiTokenBurnActivity,
]
