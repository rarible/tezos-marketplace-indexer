from datetime import datetime
from uuid import UUID

from pytz import UTC

from rarible_marketplace_indexer.models import OrderModel
from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

order_model = OrderModel(
    id=None,
    network='mainnet',
    fill='0',
    platform=PlatformEnum.FXHASH_V1,
    internal_order_id='38889',
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
    make_asset_class=AssetClassEnum.MULTI_TOKEN,
    make_contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
    make_token_id='30706',
    make_value=AssetValue(1),
    take_asset_class=AssetClassEnum.XTZ,
    take_contract=None,
    take_token_id=None,
    take_value=Xtz(35),
    origin_fees=[],
    payouts=[],
)
