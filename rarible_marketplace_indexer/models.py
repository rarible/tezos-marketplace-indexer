import uuid
from enum import Enum
from typing import Any
from typing import TypeVar
from uuid import uuid5

from dipdup.models import Model
from dipdup.models import Transaction
from tortoise import ForeignKeyFieldInstance
from tortoise import fields

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
    NFT: _StrEnumValue = 'NFT'
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


class TokenTransfer(Model):
    class Meta:
        table = 'token_transfer'

    _custom_generated_pk = True

    id = fields.BigIntField(pk=True, generated=False, required=True)
    type = fields.CharEnumField(ActivityTypeEnum)
    tzkt_token_id = fields.BigIntField(null=False)
    tzkt_transaction_id = fields.BigIntField(null=True)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    from_address = AccountAddressField(null=True)
    to_address = AccountAddressField(null=True)
    amount = AssetValueField()
    hash = OperationHashField(null=True)
    date = fields.DatetimeField(null=False)


class Ownership(Model):
    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    owner = AccountAddressField(null=False)
    balance = AssetValueField()
    updated = fields.DatetimeField(null=False)
    created = fields.DatetimeField(null=False)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    def full_id(self):
        return f"{self.contract}:{self.token_id}:{self.owner}"

    @staticmethod
    def get_id(contract, token_id, owner, *args, **kwargs):
        oid = '.'.join(map(str, filter(bool, [contract, token_id, owner])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class Token(Model):
    class Meta:
        table = 'token'

    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False)
    tzkt_id = fields.BigIntField()
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    creator = AccountAddressField(null=True)
    minted_at = fields.DatetimeField(null=False)
    minted = AssetValueField()
    supply = AssetValueField()
    deleted = fields.BooleanField(default=False)
    updated = fields.DatetimeField(null=False)
    metadata_synced = fields.BooleanField(required=True)
    royalties_synced = fields.BooleanField(required=True)
    metadata_retries = fields.IntField(required=True)
    royalties_retries = fields.IntField(required=True)
    db_updated_at = fields.DatetimeField(auto_now=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    def full_id(self):
        return f"{self.contract}:{self.token_id}"

    @staticmethod
    def get_id(contract, token_id, *args, **kwargs):
        assert contract
        assert token_id is not None

        oid = '.'.join(map(str, filter(bool, [contract, token_id])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class Collection(Model):
    class Meta:
        table = 'collection'

    _custom_generated_pk = True

    contract = AccountAddressField(pk=True, required=True)
    owner = AccountAddressField(required=True)
    metadata_synced = fields.BooleanField(required=True)
    metadata_retries = fields.IntField(required=True)
    db_updated_at = fields.DatetimeField(auto_now=True)

    def full_id(self):
        return f"{self.contract}"


class Royalties(Model):
    class Meta:
        table = "royalties"

    id = fields.UUIDField(pk=True, generated=False, required=True)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    parts = fields.JSONField()

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    @staticmethod
    def get_id(contract, token_id, *args, **kwargs):
        assert contract
        assert token_id is not None

        oid = '.'.join(map(str, filter(bool, [contract, token_id])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class CollectionMetadata(Model):
    class Meta:
        table = "metadata_collection"

    contract = AccountAddressField(pk=True, required=True)
    metadata = fields.JSONField(null=True)


class TokenMetadata(Model):
    class Meta:
        table = "metadata_token"

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False)
    contract = AccountAddressField(null=False)
    token_id = fields.TextField(null=False)
    metadata = fields.JSONField(null=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = self.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)

    @staticmethod
    def get_id(contract, token_id, *args, **kwargs):
        assert contract
        assert token_id is not None

        oid = '.'.join(map(str, filter(bool, [contract, token_id])))
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class TZProfile(Model):
    class Meta:
        table = "tzprofiles"

    account = fields.CharField(36, pk=True)
    contract = fields.CharField(36)
    valid_claims = fields.JSONField()
    invalid_claims = fields.JSONField()
    errored = fields.BooleanField()
    alias = fields.TextField(null=True)
    description = fields.TextField(null=True)
    logo = fields.TextField(null=True)
    website = fields.TextField(null=True)
    twitter = fields.CharField(max_length=256, null=True)
    domain_name = fields.TextField(null=True)
    discord = fields.CharField(max_length=256, null=True)
    github = fields.CharField(max_length=256, null=True)
    ethereum = fields.CharField(max_length=42, null=True)


class TLD(Model):
    class Meta:
        table = "tezos_domains_tld"

    id = fields.CharField(max_length=255, pk=True)
    owner = fields.CharField(max_length=36)


class Domain(Model):
    class Meta:
        table = "tezos_domains_domain"

    id = fields.CharField(max_length=255, pk=True)
    tld: ForeignKeyFieldInstance[TLD] = fields.ForeignKeyField('models.TLD', 'domains')
    owner = fields.CharField(max_length=36)
    token_id = fields.BigIntField(null=True)


class Record(Model):
    class Meta:
        table = "tezos_domains_record"

    id = fields.CharField(max_length=255, pk=True)
    domain: ForeignKeyFieldInstance[Domain] = fields.ForeignKeyField('models.Domain', 'records')
    address = fields.CharField(max_length=36, null=True)
