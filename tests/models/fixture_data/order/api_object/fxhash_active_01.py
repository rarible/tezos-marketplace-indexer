from datetime import datetime
from uuid import UUID

from pytz import UTC

from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import TokenAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import XtzAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset_type import MultiTokenAssetType
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset_type import XtzAssetType
from rarible_marketplace_indexer.types.rarible_api_objects.order.order import RaribleApiOrder
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

order_api_object = RaribleApiOrder(
    id=UUID('1b13c452-114e-5ebd-a618-9ae9bfa5403a'),
    network='mainnet',
    fill=0,
    platform=PlatformEnum.FXHASH_V1,
    status=OrderStatusEnum.ACTIVE,
    start_at=datetime(2021, 12, 22, 0, 54, 6, tzinfo=UTC),
    end_at=None,
    ended_at=None,
    cancelled=False,
    salt=24209687,
    created_at=datetime(2021, 12, 22, 0, 54, 6, tzinfo=UTC),
    last_updated_at=datetime(2021, 12, 23, 0, 54, 6, tzinfo=UTC),
    maker=ImplicitAccountAddress('tz1e9cuHbqgrJobzakykJYXUqGaPMS9vpbD2'),
    taker=None,
    make=TokenAsset(
        asset_type=MultiTokenAssetType(
            contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
            token_id='176675',
        ),
        asset_value=AssetValue(1),
    ),
    take=XtzAsset(
        asset_type=XtzAssetType(),
        asset_value=Xtz(9),
    ),
)
