# generated by datamodel-codegen:
#   filename:  storage.json

from __future__ import annotations

from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Extra


class Token(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class CurrencyItem(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class Auctions(BaseModel):
    class Config:
        extra = Extra.forbid

    token: Token
    token_amount: str
    end_timestamp: str
    seller: str
    bid_amount: str
    bidder: str
    currency: Optional[CurrencyItem]
    require_verified: bool


class Key(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class CollectedFa2Fee(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key
    value: str


class Key1(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class Fa2Fee(BaseModel):
    class Config:
        extra = Extra.forbid

    key: Key1
    value: str


class LastCollectOp(BaseModel):
    class Config:
        extra = Extra.forbid

    level: str
    source: str


class Token1(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class CurrencyItem1(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class Offers(BaseModel):
    class Config:
        extra = Extra.forbid

    token: Token1
    token_amount: str
    buyer: str
    price_in_nat: str
    currency: Optional[CurrencyItem1]
    require_verified: bool


class Token2(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class CurrencyItem2(BaseModel):
    class Config:
        extra = Extra.forbid

    address: str
    nat: str


class Swaps(BaseModel):
    class Config:
        extra = Extra.forbid

    token: Token2
    currency: Optional[CurrencyItem2]
    token_left_amount: str
    token_start_amount: str
    seller: str
    starting_price_in_nat: str
    ending_price_in_nat: str
    collect_max_per_tx: str
    require_verified: bool
    ending_time: Optional[str]
    burn_on_end: bool


class VersumV1Storage(BaseModel):
    class Config:
        extra = Extra.forbid

    admin_check_lambda: str
    administrator: str
    auction_counter: str
    auctions: Dict[str, Auctions]
    collected_fa2_fees: List[CollectedFa2Fee]
    collected_xtz_fees: str
    contract_registry: str
    default_fa2_fee: str
    default_platform_fee: str
    default_xtz_fee: str
    deprecated: bool
    extra_db: Dict[str, str]
    fa2_fees: List[Fa2Fee]
    fee_per_platform: Dict[str, str]
    identity: str
    last_collect_op: LastCollectOp
    max_fee: str
    metadata: Dict[str, str]
    min_fee: str
    offer_counter: str
    offers: Dict[str, Offers]
    paused: bool
    royalty_adapter: str
    swap_counter: str
    swaps: Dict[str, Swaps]
    big_map: Dict[str, str]
