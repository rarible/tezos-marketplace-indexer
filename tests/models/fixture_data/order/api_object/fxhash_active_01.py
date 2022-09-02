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
    id=UUID('a2beb69a-a505-5a6c-a75a-83e66ac477af'),
    network='mainnet',
    fill=0,
    platform=PlatformEnum.FXHASH_V1,
    status=OrderStatusEnum.ACTIVE,
    start_at=datetime(2021, 12, 6, 9, 39, 20, tzinfo=UTC),
    end_at=None,
    ended_at=None,
    cancelled=False,
    salt=22385716,
    created_at=datetime(2021, 12, 6, 9, 39, 20, tzinfo=UTC),
    last_updated_at=datetime(2021, 12, 6, 9, 39, 20, tzinfo=UTC),
    maker=ImplicitAccountAddress('tz1gfc1S3RQoMeQNnbs61NxomqjKbMQZCLoc'),
    taker=None,
    make=TokenAsset(
        asset_type=MultiTokenAssetType(
            contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
            token_id='30706',
        ),
        asset_value=AssetValue(1),
    ),
    take=XtzAsset(
        asset_type=XtzAssetType(),
        asset_value=Xtz(35),
    ),
    origin_fees=[],
    payouts=[],
)
