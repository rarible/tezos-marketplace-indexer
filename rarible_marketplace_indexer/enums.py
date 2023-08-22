from enum import Enum
from typing import TypeVar

_StrEnumValue = TypeVar("_StrEnumValue")


class TransactionTypeEnum(str, Enum):
    SALE: _StrEnumValue = 'SALE'
    BID: _StrEnumValue = 'BID'
    FLOOR_BID: _StrEnumValue = 'FLOOR_BID'


class OrderStatusEnum(str, Enum):
    ACTIVE: _StrEnumValue = 'ACTIVE'
    FILLED: _StrEnumValue = 'FILLED'
    HISTORICAL: _StrEnumValue = 'HISTORICAL'
    INACTIVE: _StrEnumValue = 'INACTIVE'
    CANCELLED: _StrEnumValue = 'CANCELLED'


class ActivityTypeEnum(str, Enum):
    GET_BID: _StrEnumValue = 'GET_BID'
    GET_FLOOR_BID: _StrEnumValue = 'GET_FLOOR_BID'
    ORDER_LIST: _StrEnumValue = 'LIST'
    ORDER_MATCH: _StrEnumValue = 'SELL'
    ORDER_CANCEL: _StrEnumValue = 'CANCEL_LIST'
    CANCEL_BID: _StrEnumValue = 'CANCEL_BID'
    CANCEL_FLOOR_BID: _StrEnumValue = 'CANCEL_FLOOR_BID'
    MAKE_BID: _StrEnumValue = 'MAKE_BID'
    MAKE_FLOOR_BID: _StrEnumValue = 'MAKE_FLOOR_BID'
    TOKEN_MINT: _StrEnumValue = 'MINT'
    TOKEN_TRANSFER: _StrEnumValue = 'TRANSFER'
    TOKEN_BURN: _StrEnumValue = 'BURN'


class PlatformEnum(str, Enum):
    HEN: _StrEnumValue = 'HEN'
    TEIA_V1: _StrEnumValue = 'TEIA_V1'
    VERSUM_V1: _StrEnumValue = 'VERSUM_V1'
    OBJKT_V1: _StrEnumValue = 'OBJKT_V1'
    OBJKT_V2: _StrEnumValue = 'OBJKT_V2'
    RARIBLE_V1: _StrEnumValue = 'RARIBLE_V1'
    RARIBLE_V2: _StrEnumValue = 'RARIBLE_V2'
    FXHASH_V1: _StrEnumValue = 'FXHASH_V1'
    FXHASH_V2: _StrEnumValue = 'FXHASH_V2'


class IndexEnum(str, Enum):
    COLLECTION: _StrEnumValue = 'COLLECTION'
    COLLECTION_METADATA: _StrEnumValue = 'COLLECTION_METADATA'
    NFT: _StrEnumValue = 'NFT'
    NFT_METADATA: _StrEnumValue = 'NFT_METADATA'
    LEGACY_ORDERS: _StrEnumValue = 'LEGACY_ORDERS'
    V1_CLEANING: _StrEnumValue = 'V1_CLEANING'
    V1_FILL_FIX: _StrEnumValue = 'V1_FILL_FIX'


class TaskStatus(str, Enum):
    NEW: _StrEnumValue = 'NEW'
    RUNNING: _StrEnumValue = 'RUNNING'
    FINISHED: _StrEnumValue = 'FINISHED'
    FAILED: _StrEnumValue = 'FAILED'