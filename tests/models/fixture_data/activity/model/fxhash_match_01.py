from datetime import datetime
from uuid import UUID

from pytz import UTC

from rarible_marketplace_indexer.models import Activity
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OperationHash
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

activity_model = Activity(
    type=ActivityTypeEnum.ORDER_MATCH,
    network='mainnet',
    platform=PlatformEnum.FXHASH_V1,
    order_id=UUID('702b483c-8b5f-5731-b1ad-ce4c10b24743'),
    internal_order_id=45488,
    maker=ImplicitAccountAddress('tz1Ms3JA2ZUSBNKqVABoGpeg3gv2e685XWvf'),
    taker=ImplicitAccountAddress('tz1QjzQd8AuAbLKLa9Jp7bYp3gPrrTsHxDSe'),
    make_asset_class=AssetClassEnum.MULTI_TOKEN,
    make_contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
    make_token_id=128493,
    make_value=1,
    make_price=AssetValue(9),
    take_asset_class=AssetClassEnum.XTZ,
    take_contract=None,
    take_token_id=None,
    take_value=Xtz(9),
    take_price=None,
    operation_level=1926242,
    operation_timestamp=datetime(2021, 12, 7, 21, 23, 10, tzinfo=UTC),
    operation_hash=OperationHash('onqH9Z8T54frxN3j9HfoZRdkJKFGeKaJ6yz8ZkCGRSgH7u185Tt'),
    operation_counter=30923686,
    operation_nonce=None,
)
