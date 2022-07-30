from datetime import datetime
from uuid import UUID

from pytz import UTC

from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.activity import RaribleApiOrderMatchActivity
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import TokenAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import XtzAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset_type import MultiTokenAssetType
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset_type import XtzAssetType
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OperationHash
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

activity_api_object = RaribleApiOrderMatchActivity(
    id=UUID('0412dbe9-ae58-543c-9a02-04974ccec9af'),
    network='mainnet',
    type=ActivityTypeEnum.ORDER_MATCH,
    source=PlatformEnum.FXHASH_V1,
    order_id=UUID('702b483c-8b5f-5731-b1ad-ce4c10b24743'),
    hash=OperationHash('onqH9Z8T54frxN3j9HfoZRdkJKFGeKaJ6yz8ZkCGRSgH7u185Tt'),
    date=datetime(2021, 12, 7, 21, 23, 10, tzinfo=UTC),
    reverted=False,
    nft=TokenAsset(
        asset_type=MultiTokenAssetType(
            contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
            token_id='128493',
        ),
        asset_value=AssetValue(1),
    ),
    payment=XtzAsset(
        asset_type=XtzAssetType(),
        asset_value=Xtz(9),
    ),
    buyer=ImplicitAccountAddress('tz1QjzQd8AuAbLKLa9Jp7bYp3gPrrTsHxDSe'),
    seller=ImplicitAccountAddress('tz1Ms3JA2ZUSBNKqVABoGpeg3gv2e685XWvf'),
)
