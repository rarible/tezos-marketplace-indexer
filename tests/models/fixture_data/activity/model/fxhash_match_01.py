from datetime import datetime
from uuid import UUID

from pytz import UTC

from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OperationHash
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

activity_model = ActivityModel(
    type=ActivityTypeEnum.ORDER_MATCH,
    network='mainnet',
    platform=PlatformEnum.FXHASH_V1,
    order_id=UUID('a2aa3ae7-6888-520b-9205-72176ec5fa83'),
    internal_order_id=47,
    maker=ImplicitAccountAddress('tz1XT3ncKE9KRzn2qWFmcG3Fg5hAhtKUF8hU'),
    taker=ImplicitAccountAddress('tz1ewF2P3erZJSP8m35QiNEKGtwj7qsBhF8z'),
    make_asset_class=AssetClassEnum.MULTI_TOKEN,
    make_contract=OriginatedAccountAddress('KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE'),
    make_token_id=1089,
    make_value=1,
    take_asset_class=AssetClassEnum.XTZ,
    take_contract=None,
    take_token_id=None,
    take_value=Xtz(10),
    operation_level=1853788,
    operation_timestamp=datetime(2021, 11, 11, 5, 37, 58, tzinfo=UTC),
    operation_hash=OperationHash('oozmc8oXQSE5cYASkXCAFm5kwR5DTfNU4fi33BNuhN7UM4Fpd5o'),
    operation_counter=38911117,
    operation_nonce=1,
)
