import uuid
from enum import Enum
from typing import Any
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from uuid import uuid5

from aiosignal import Signal
from dipdup.models import Model
from dipdup.models import Transaction
from tortoise import fields
from tortoise.backends.base.client import BaseDBAsyncClient
from tortoise.signals import post_delete
from tortoise.signals import post_save

from rarible_marketplace_indexer.producer.helper import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValueField
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import AccountAddressField
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OperationHashField

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
    LEGACY_ORDERS: _StrEnumValue = 'LEGACY_ORDERS'
    V1_CLEANING: _StrEnumValue = 'V1_CLEANING'
    V1_FILL_FIX: _StrEnumValue = 'V1_FILL_FIX'


class ActivityModel(Model):
    class Meta:
        table = 'marketplace_activity'

    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True, default=None)
    order_id = fields.UUIDField(required=True, index=True)
    type = fields.CharEnumField(ActivityTypeEnum)
    network = fields.CharField(max_length=16)
    platform = fields.CharEnumField(PlatformEnum)
    internal_order_id = fields.CharField(max_length=32, index=True)
    maker = AccountAddressField(null=True)
    taker = AccountAddressField(null=True)
    make_asset_class = fields.CharEnumField(AssetClassEnum)
    make_contract = AccountAddressField(null=True)
    make_token_id = fields.TextField(null=True)
    make_value = AssetValueField()
    take_asset_class = fields.CharEnumField(AssetClassEnum, null=True)
    take_contract = AccountAddressField(null=True)
    take_token_id = fields.TextField(null=True)
    take_value = AssetValueField(null=True)

    operation_level = fields.IntField()
    operation_timestamp = fields.DatetimeField()
    operation_hash = OperationHashField()
    operation_counter = fields.IntField()
    operation_nonce = fields.IntField(null=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    @staticmethod
    def get_id(operation_hash, operation_counter, operation_nonce, order_id, *args, **kwargs):
        assert operation_hash
        assert operation_counter
        assert order_id

        oid = '.'.join(map(str, filter(bool, [operation_hash, operation_counter, operation_nonce, order_id])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)

    def apply(self, transaction: Transaction):
        new_id = self.get_id(transaction.data.hash, transaction.data.counter, transaction.data.nonce, self.order_id)
        activity = self.clone(pk=new_id)

        activity.operation_level = transaction.data.level
        activity.operation_timestamp = transaction.data.timestamp
        activity.operation_hash = transaction.data.hash
        activity.operation_counter = transaction.data.counter
        activity.operation_nonce = transaction.data.nonce

        return activity


class OrderModel(Model):
    class Meta:
        table = 'marketplace_order'

    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True)
    network = fields.CharField(max_length=16, index=True)
    fill = AssetValueField(default=0)
    platform = fields.CharEnumField(PlatformEnum, index=True)
    internal_order_id = fields.CharField(max_length=32, index=True)
    status = fields.CharEnumField(OrderStatusEnum, index=True)
    start_at = fields.DatetimeField()
    end_at = fields.DatetimeField(null=True)
    cancelled = fields.BooleanField(default=False)
    salt = fields.TextField()
    created_at = fields.DatetimeField(index=True)
    ended_at = fields.DatetimeField(null=True)
    last_updated_at = fields.DatetimeField(index=True)
    maker = AccountAddressField()
    taker = AccountAddressField(null=True)
    make_asset_class = fields.CharEnumField(AssetClassEnum)
    make_contract = AccountAddressField(null=True)
    make_token_id = fields.TextField(null=True)
    make_value = AssetValueField()
    make_price = AssetValueField(null=True)
    take_asset_class = fields.CharEnumField(AssetClassEnum, null=True)
    take_contract = AccountAddressField(null=True)
    take_token_id = fields.TextField(null=True)
    take_value = AssetValueField(null=True)
    take_price = AssetValueField(null=True)
    origin_fees = fields.JSONField()
    payouts = fields.JSONField()

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    @staticmethod
    def get_id(network, platform, internal_order_id, maker, created_at, *args, **kwargs):
        assert network
        assert platform
        assert internal_order_id
        assert maker
        assert created_at

        oid = '.'.join(map(str, filter(bool, [network, platform, internal_order_id, maker, created_at])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class IndexingStatus(Model):
    class Meta:
        table = 'indexing_status'

    index = fields.CharEnumField(IndexEnum, index=True, pk=True, required=True)
    last_level = fields.TextField()


class LegacyOrderModel(Model):
    class Meta:
        table = 'legacy_orders'

    hash = fields.CharField(index=True, pk=True, required=True, max_length=64)
    id = fields.UUIDField(generated=False, required=True)
    data = fields.JSONField()


@post_save(OrderModel)
async def signal_order_post_save(
    sender: OrderModel,
    instance: OrderModel,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.order.factory import RaribleApiOrderFactory

    await producer_send(RaribleApiOrderFactory.build(instance))


@post_save(ActivityModel)
async def signal_activity_post_save(
    sender: ActivityModel,
    instance: ActivityModel,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.factory import RaribleApiOrderActivityFactory

    await producer_send(RaribleApiOrderActivityFactory.build(instance))


class TokenTransfer(Model):
    class Meta:
        table = 'token_transfer'

    _custom_generated_pk = True

    id = fields.IntField(pk=True, generated=False, required=True)
    type = fields.CharEnumField(ActivityTypeEnum)
    tzkt_token_id = fields.IntField(null=False)
    tzkt_transaction_id = fields.IntField(null=True)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    from_address = AccountAddressField(null=True)
    to_address = AccountAddressField(null=True)
    amount = AssetValueField()
    hash = OperationHashField(null=True)
    date = fields.DatetimeField(null=False)


@post_save(TokenTransfer)
async def signal_token_transfer_post_save(
    sender: TokenTransfer,
    instance: TokenTransfer,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.factory import RaribleApiTokenActivityFactory

    if instance.type == ActivityTypeEnum.TOKEN_MINT:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_mint_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_BURN:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_burn_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_TRANSFER:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_transfer_activity(instance)
    await producer_send(token_transfer_activity)


class Ownership(Model):
    id = fields.IntField(pk=True)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    owner = AccountAddressField(null=False)
    balance = AssetValueField()
    updated = fields.DatetimeField(null=False)

    def full_id(self):
        return f"{self.contract}:{self.token_id}:{self.owner}"


@post_save(Ownership)
async def signal_ownership_post_save(
    sender: Ownership,
    instance: Ownership,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    event = RaribleApiOwnershipFactory.build_update(instance)
    await producer_send(event)


@post_delete(Ownership)
async def signal_ownership_post_delete(sender: "Type[Signal]", instance: Ownership, using_db: "Optional[BaseDBAsyncClient]") -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    event = RaribleApiOwnershipFactory.build_delete(instance)
    await producer_send(event)


class Token(Model):
    class Meta:
        table = 'token'

    _custom_generated_pk = True

    id = fields.IntField(pk=True, generated=False, required=True)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    minted_at = fields.DatetimeField(null=False)
    minted = AssetValueField()
    supply = AssetValueField()
    deleted = fields.BooleanField(default=False)
    updated = fields.DatetimeField(null=False)
    metadata = fields.JSONField(null=True)
