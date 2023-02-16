import asyncio
import uuid
import datetime
from typing import Any, List
from uuid import uuid5

from tortoise import ForeignKeyFieldInstance
from tortoise import fields
from tortoise.signals import post_save, post_delete, pre_save

from dipdup.models import Model
from dipdup.models import Transaction
from rarible_marketplace_indexer.enums import ActivityTypeEnum, PlatformEnum, OrderStatusEnum, IndexEnum
from rarible_marketplace_indexer.producer.container import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValueField
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import AccountAddressField
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OperationHashField


class Activity(Model):
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
    make_token_id = fields.CharField(max_length=256, null=True)
    make_value = AssetValueField()
    make_price = AssetValueField(null=True)
    take_asset_class = fields.CharEnumField(AssetClassEnum, null=True)
    take_contract = AccountAddressField(null=True)
    take_token_id = fields.CharField(max_length=256, null=True)
    take_value = AssetValueField(null=True)
    take_price = AssetValueField(null=True)
    operation_level = fields.IntField()
    operation_timestamp = fields.DatetimeField()
    operation_hash = OperationHashField()
    operation_counter = fields.IntField()
    operation_nonce = fields.IntField(null=True)

    db_updated_at = fields.DatetimeField(null=True)

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


class Order(Model):
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
    make_token_id = fields.CharField(max_length=256, null=True)
    make_value = AssetValueField()
    make_price = AssetValueField(null=True)
    take_asset_class = fields.CharEnumField(AssetClassEnum, null=True)
    take_contract = AccountAddressField(null=True)
    take_token_id = fields.CharField(max_length=256, null=True)
    take_value = AssetValueField(null=True)
    take_price = AssetValueField(null=True)
    origin_fees = fields.JSONField()
    payouts = fields.JSONField()
    is_bid = fields.BooleanField(default=False, null=False)

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

    index = fields.CharEnumField(IndexEnum, index=True, pk=True, required=True, max_length=20)
    last_level = fields.TextField()


class LegacyOrder(Model):
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
    tzkt_origination_id = fields.BigIntField(null=True)
    contract = AccountAddressField(null=False)
    token_id = fields.CharField(max_length=256, null=False)
    from_address = AccountAddressField(null=True)
    to_address = AccountAddressField(null=True)
    amount = AssetValueField()
    hash = OperationHashField(null=True)
    date = fields.DatetimeField(null=False)
    db_updated_at = fields.DatetimeField(null=True)


class Ownership(Model):
    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False)
    contract = AccountAddressField(null=False)
    token_id = fields.CharField(max_length=256, null=False)
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
        oid = f"{contract}:{token_id}:{owner}"
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class Token(Model):
    class Meta:
        table = 'token'

    _custom_generated_pk = True

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False, index=True)
    tzkt_id = fields.BigIntField()
    contract = AccountAddressField(null=False)
    token_id = fields.CharField(max_length=256, null=False)
    creator = AccountAddressField(null=True, index=True)
    minted_at = fields.DatetimeField(null=False)
    minted = AssetValueField()
    supply = AssetValueField()
    deleted = fields.BooleanField(default=False)
    updated = fields.DatetimeField(null=False)
    db_updated_at = fields.DatetimeField(required=True)

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

        oid = f"{contract}:{token_id}"
        return uuid5(namespace=uuid.NAMESPACE_OID, name=oid)


class Collection(Model):
    class Meta:
        table = 'collection'

    _custom_generated_pk = True

    id = AccountAddressField(pk=True, required=True)
    owner = AccountAddressField(required=True)
    minters = fields.JSONField(required=True)
    standard = fields.CharField(3, required=True)
    symbol = fields.CharField(20, null=True)
    db_updated_at = fields.DatetimeField(required=True, index=True)

    def full_id(self):
        return f"{self.contract}"


class Royalties(Model):
    class Meta:
        table = "royalties"

    id = fields.UUIDField(pk=True, generated=False, required=True, index=True)
    contract = AccountAddressField(null=False, index=True)
    token_id = fields.CharField(max_length=256, null=False)
    parts = fields.JSONField(null=False)
    royalties_synced = fields.BooleanField(required=True, index=True)
    royalties_retries = fields.IntField(required=True, index=True)
    db_updated_at = fields.DatetimeField(required=True, index=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = Token.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)


class CollectionMetadata(Model):
    class Meta:
        table = "metadata_collection"

    id = AccountAddressField(pk=True, required=True, index=True)
    metadata = fields.TextField(null=True)
    metadata_synced = fields.BooleanField(required=True, index=True)
    metadata_retries = fields.IntField(required=True, index=True)
    db_updated_at = fields.DatetimeField(required=True, index=True)


class TokenMetadata(Model):
    class Meta:
        table = "metadata_token"

    id = fields.UUIDField(pk=True, generated=False, required=True, null=False, index=True)
    contract = AccountAddressField(null=False, index=True)
    token_id = fields.CharField(max_length=256, null=False)
    metadata = fields.TextField(null=True)
    metadata_synced = fields.BooleanField(required=True, index=True)
    metadata_retries = fields.IntField(required=True, index=True)
    db_updated_at = fields.DatetimeField(required=True)

    def __init__(self, **kwargs: Any) -> None:
        try:
            kwargs['id'] = Token.get_id(**kwargs)
        except TypeError:
            pass
        super().__init__(**kwargs)


class AggregatorEvent(Model):
    class Meta:
        table = "aggregator_event"

    id = fields.BigIntField(pk=True, generated=False, required=True, index=True)
    tracker = fields.CharField(max_length=256, null=False, index=True)
    level = fields.IntField(required=True, index=True)
    operation_hash = OperationHashField()


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


class Tasks(Model):
    class Meta:
        table = 'tasks'

    id = fields.BigIntField(pk=True, generated=True, required=True)
    name = fields.CharField(max_length=50, null=False)
    param = fields.TextField(null=True)
    sample = fields.TextField(null=True)
    version = fields.IntField(null=False, default="1")
    error = fields.TextField(null=True)
    status = fields.CharField(max_length=50, null=False, default="NEW")
    created = fields.DatetimeField(null=False, auto_now_add=True)
    updated = fields.DatetimeField(null=False, auto_now=True)


@post_save(Order)
async def signal_order_post_save(
    sender: Order,
    instance: Order,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.order.factory import RaribleApiOrderFactory
    # workaround: get time for db to save tx
    if not instance.platform in [PlatformEnum.RARIBLE_V1, PlatformEnum.RARIBLE_V2]:
        await asyncio.sleep(125)
    else:
        await asyncio.sleep(10)
    await producer_send(RaribleApiOrderFactory.build(instance))


@post_save(Collection)
async def signal_collection_post_save(
    sender: Collection,
    instance: Collection,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.collection.factory import RaribleApiCollectionFactory
    await producer_send(RaribleApiCollectionFactory.build(instance))


@pre_save(Activity)
async def signal_activity_transfer_pre_save(sender, instance: Activity, *args, **kwargs) -> None:
    # we need to truncate microsecond for proper continuation working
    instance.db_updated_at = get_truncated_now()


@post_save(Activity)
async def signal_activity_post_save(
    sender: Activity,
    instance: Activity,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.factory import (
        RaribleApiOrderActivityFactory,
    )

    await producer_send(RaribleApiOrderActivityFactory.build(instance))


@pre_save(TokenTransfer)
async def signal_token_transfer_pre_save(sender, instance: TokenTransfer, *args, **kwargs) -> None:
    # we need to truncate microsecond for proper continuation working
    instance.db_updated_at = get_truncated_now()


@pre_save(Royalties)
async def signal_royalties_pre_save(sender, instance: Activity, *args, **kwargs) -> None:
    # we need to truncate microsecond for proper continuation working
    instance.db_updated_at = get_truncated_now()


@post_save(TokenTransfer)
async def signal_token_transfer_post_save(
    sender: TokenTransfer,
    instance: TokenTransfer,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.factory import (
        RaribleApiTokenActivityFactory,
    )

    if instance.type == ActivityTypeEnum.TOKEN_MINT:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_mint_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_BURN:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_burn_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_TRANSFER:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_transfer_activity(instance)
    await producer_send(token_transfer_activity)


@post_save(Ownership)
async def signal_ownership_post_save(
    sender: Ownership,
    instance: Ownership,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    if instance.balance > 0:
        event = RaribleApiOwnershipFactory.build_update(instance)
        await producer_send(event)


@post_delete(Ownership)
async def signal_ownership_post_delete(
    sender: "Type[Signal]", instance: Ownership, using_db: "Optional[BaseDBAsyncClient]"
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    event = RaribleApiOwnershipFactory.build_delete(instance)
    await producer_send(event)


@post_save(Token)
async def signal_token_post_save(
    sender: Token,
    instance: Token,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.token.factory import RaribleApiTokenFactory

    if instance.deleted:
        event = RaribleApiTokenFactory.build_delete(instance)
    else:
        event = RaribleApiTokenFactory.build_update(instance)
    await producer_send(event)


def get_truncated_now():
    now = datetime.datetime.now(datetime.timezone.utc)
    milliseconds = now.microsecond % 1000 * 1000
    return now.replace(microsecond=milliseconds)
