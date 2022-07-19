from dataclasses import field
from datetime import datetime
from typing import List
from typing import Optional

from pydantic.dataclasses import dataclass

from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.base_value import BaseValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


@dataclass
class MakeDto:
    asset_class: AssetClassEnum
    contract: Optional[OriginatedAccountAddress]
    token_id: Optional[int]
    value: AssetValue


@dataclass
class TakeDto:
    asset_class: AssetClassEnum
    contract: Optional[OriginatedAccountAddress]
    token_id: Optional[int]
    value: BaseValue


@dataclass
class ListDto:
    internal_order_id: str
    maker: ImplicitAccountAddress
    make: MakeDto
    take: TakeDto
    start_at: Optional[datetime] = None  # for marketplaces with the possibility of a delayed start of sales
    end_at: Optional[datetime] = None  # for marketplaces with the possibility of sales expiration
    origin_fees: List[Part] = field(default_factory=list)
    payouts: List[Part] = field(default_factory=list)


@dataclass
class CancelDto:
    internal_order_id: str


@dataclass
class MatchDto:
    internal_order_id: str
    taker: ImplicitAccountAddress
    token_id: Optional[int]
    match_amount: Optional[AssetValue]
    match_timestamp: datetime
    origin_fees: List[Part] = field(default_factory=list)
    payouts: List[Part] = field(default_factory=list)


@dataclass
class LegacyMatchDto:

    internal_order_id: str
    maker: ImplicitAccountAddress
    taker: ImplicitAccountAddress
    make: MakeDto
    take: TakeDto
    match_timestamp: datetime
    token_id: Optional[int]
    match_amount: Optional[AssetValue]
    start: Optional[datetime] = None  # for marketplaces with the possibility of a delayed start of sales
    end_at: Optional[datetime] = None  # for marketplaces with the possibility of sales expiration
    origin_fees: List[Part] = field(default_factory=list)
    payouts: List[Part] = field(default_factory=list)

@dataclass
class LegacyCancelDto:
    contract: OriginatedAccountAddress
    token_id: str
    maker: ImplicitAccountAddress
    salt: str