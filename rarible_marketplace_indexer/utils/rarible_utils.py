import json
import logging
import os
import random
import string
import urllib
import uuid
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid5

import requests
from base58 import b58encode_check
from dipdup.context import DipDupContext
from pytezos import MichelsonType
from pytezos import michelson_to_micheline
from requests import Response

from rarible_marketplace_indexer.event.dto import MakeDto
from rarible_marketplace_indexer.event.dto import TakeDto
from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import LegacyOrderModel
from rarible_marketplace_indexer.models import OrderModel
from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.models import TransactionTypeEnum
from rarible_marketplace_indexer.prometheus.rarible_metrics import RaribleMetrics
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.activity import RaribleApiOrderCancelActivity
from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.activity import RaribleApiOrderListActivity
from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.activity import RaribleApiOrderMatchActivity
from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.activity import RaribleApiTokenActivity
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import TokenAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import RaribleApiCollection
from rarible_marketplace_indexer.types.rarible_api_objects.order.order import RaribleApiOrder
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.ownership import RaribleApiOwnership
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import RaribleApiToken
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


def get_json_parts(parts: List[Part]):
    json_parts: List[Part] = []
    for part in parts:
        json_parts.append({'part_account': part.part_account, 'part_value': part.part_value})
    return json_parts


def generate_random_unique_ophash(size=50, chars=(string.ascii_lowercase + string.ascii_uppercase + string.digits)):
    return ''.join(random.choice(chars) for _ in range(size))


def reconcile_item(contract, token_id):
    logger = logging.getLogger('dipdup.reconcile')
    response = requests.post(
        f"{os.getenv('UNION_API')}/v0.1/refresh/item/TEZOS:{contract}:{token_id}/reconcile?full=true"
    )
    if not response.ok:
        logger.info(f"{contract}:{token_id} need reconcile: Error {response.status_code} - {response.reason}")
    else:
        logger.info(f"{contract}:{token_id} synced properly after legacy cancel")


class RaribleUtils:
    unpack_map_take: Dict[int, str] = {
        0: '_take_xtz',
        1: '_take_fa12',
        2: '_take_fa2',
    }

    unpack_map_make: Dict[int, str] = {
        0: '_make_xtz',
        1: '_make_fa12',
        2: '_make_fa2',
    }

    @classmethod
    def _get_contract(cls, asset_bytes: bytes, offset: int) -> OriginatedAccountAddress:
        header = bytes.fromhex('025a79')
        return OriginatedAccountAddress(b58encode_check(header + asset_bytes[offset : offset + 20]).decode())

    @classmethod
    def _get_token_id(cls, asset_bytes: bytes) -> int:
        data, token_id, length = asset_bytes[31:], 0, 1

        while data[length - 1] & 0b10000000 != 0:
            length += 1

        for i in range(length - 1, 0, -1):
            token_id <<= 7
            token_id |= data[i] & 0b01111111

        token_id <<= 6
        token_id |= data[0] & 0b00111111

        if (data[0] & 0b01000000) != 0:
            token_id = -token_id

        return token_id

    @classmethod
    def _take_xtz(cls, value: int, asset_bytes: Optional[bytes] = None) -> TakeDto:
        assert not asset_bytes

        return TakeDto(asset_class=AssetClassEnum.XTZ, contract=None, token_id=None, value=Xtz.from_u_tezos(value))

    @classmethod
    def _take_fa12(cls, value: int, asset_bytes: bytes) -> TakeDto:
        return TakeDto(
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            contract=cls._get_contract(asset_bytes, 7),
            token_id=0,
            value=AssetValue(value),
        )

    @classmethod
    def _take_fa2(cls, value: int, asset_bytes: bytes) -> TakeDto:
        return TakeDto(
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            contract=cls._get_contract(asset_bytes, 9),
            token_id=cls._get_token_id(asset_bytes),
            value=AssetValue(value),
        )

    @classmethod
    def _make_xtz(cls, value: int, asset_bytes: Optional[bytes] = None) -> TakeDto:
        assert not asset_bytes

        return MakeDto(asset_class=AssetClassEnum.XTZ, contract=None, token_id=None, value=Xtz.from_u_tezos(value))

    @classmethod
    def _make_fa12(cls, value: int, asset_bytes: bytes) -> TakeDto:
        return MakeDto(
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            contract=cls._get_contract(asset_bytes, 7),
            token_id=0,
            value=AssetValue(value),
        )

    @classmethod
    def _make_fa2(cls, value: int, asset_bytes: bytes) -> TakeDto:
        return MakeDto(
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            contract=cls._get_contract(asset_bytes, 9),
            token_id=cls._get_token_id(asset_bytes),
            value=AssetValue(value),
        )

    @staticmethod
    def get_order_hash(
        contract: OriginatedAccountAddress,
        token_id: int,
        seller: ImplicitAccountAddress,
        platform: PlatformEnum,
        asset_class: str = None,
        asset: str = None,
    ) -> str:
        return uuid5(
            namespace=uuid.NAMESPACE_OID,
            name=f'{platform}/{TransactionTypeEnum.SALE}-{contract}:{token_id}@{seller}/{asset_class}-{asset}',
        ).hex

    @staticmethod
    def get_bid_hash(
        contract: OriginatedAccountAddress,
        token_id: int,
        bidder: ImplicitAccountAddress,
        platform: PlatformEnum,
        asset_class: str = None,
        asset: str = None,
    ) -> str:
        return uuid5(
            namespace=uuid.NAMESPACE_OID,
            name=f'{platform}/{TransactionTypeEnum.BID}-{contract}:{token_id}@{bidder}/{asset_class}-{asset}',
        ).hex

    @staticmethod
    def get_floor_bid_hash(
        contract: OriginatedAccountAddress,
        bidder: ImplicitAccountAddress,
        platform: PlatformEnum,
        asset_class: str = None,
        asset: str = None,
    ) -> str:
        return uuid5(
            namespace=uuid.NAMESPACE_OID,
            name=f'{platform}/{TransactionTypeEnum.FLOOR_BID}-{contract}@{bidder}/{asset_class}-{asset}',
        ).hex

    @classmethod
    def get_take_dto(cls, sale_type: int, value: int, asset_bytes: Optional[bytes] = None) -> TakeDto:
        method_name = cls.unpack_map_take.get(sale_type)
        take_method = getattr(cls, method_name)
        return take_method(value, asset_bytes)

    @classmethod
    def get_make_dto(cls, sale_type: int, value: int, asset_bytes: Optional[bytes] = None) -> MakeDto:
        method_name = cls.unpack_map_make.get(sale_type)
        make_method = getattr(cls, method_name)
        return make_method(value, asset_bytes)


async def import_legacy_order(order: dict):
    order = json.loads(order["data"])
    logger = logging.getLogger('dipdup.legacy')
    logger.info(f"Importing order: {order}")

    date_pattern = "%Y-%m-%dT%H:%M:%SZ"

    make = MakeDto(
        asset_class=AssetClassEnum.MULTI_TOKEN,
        contract=OriginatedAccountAddress(order["make"]["assetType"]["contract"]),
        token_id=int(order["make"]["assetType"]["tokenId"]),
        value=AssetValue(order["make"]["value"]),
    )

    take_type = AssetClassEnum.XTZ
    asset_type = None
    asset = b""
    asset_object = None
    if order["take"]["assetType"]["assetClass"] == "FA_1_2":
        take_type = AssetClassEnum.FUNGIBLE_TOKEN
        asset_type = MichelsonType.match(michelson_to_micheline('address'))

        asset_object = order["take"]["assetType"]["assetClass"]["contract"]
    elif order["take"]["assetType"]["assetClass"] == "FA_2":
        take_type = AssetClassEnum.FUNGIBLE_TOKEN
        asset_type = MichelsonType.match(michelson_to_micheline('pair address nat'))
        asset_object = (
            order["take"]["assetType"]["assetClass"]["contract"],
            order["take"]["assetType"]["assetClass"]["tokenId"],
        )

    if asset_type is not None:
        asset = asset_type.from_python_object(asset_object).pack().hex()

    take_token_id = order["take"]["assetType"].get("tokenId")
    if take_token_id is not None:
        take_token_id = int(order["take"]["assetType"].get("tokenId"))

    take_contract = order["take"]["assetType"].get("contract")
    if take_contract is not None:
        take_contract = OriginatedAccountAddress(order["take"]["assetType"].get("contract"))

    take = TakeDto(
        asset_class=take_type, contract=take_contract, token_id=take_token_id, value=AssetValue(order["take"]["value"])
    )

    internal_order_id = RaribleUtils.get_order_hash(
        contract=OriginatedAccountAddress(make.contract),
        token_id=int(make.token_id),
        seller=ImplicitAccountAddress(order["maker"]),
        platform=PlatformEnum.RARIBLE_V1,
        asset_class=take_type,
        asset=asset,
    )

    start_at = order.get("start")
    if start_at is None:
        start_at = datetime.strptime(order["createdAt"], date_pattern)
    else:
        if type(start_at) is str:
            start_at = datetime.strptime(order["start"], date_pattern)
        else:
            datetime.fromtimestamp(order["start"])

    end_at = order.get("end")
    if end_at is not None:
        if type(end_at) is str:
            end_at = datetime.strptime(order["end"], date_pattern)
        else:
            datetime.fromtimestamp(order["end"])

    origin_fees = []
    payouts = []

    for fee in order["data"]["originFees"]:
        origin_fees.append(Part(part_account=fee["account"], part_value=fee["value"]))

    for fee in order["data"]["payouts"]:
        payouts.append(Part(part_account=fee["account"], part_value=fee["value"]))

    order_model = await OrderModel.get_or_none(
        internal_order_id=internal_order_id,
        network=os.getenv('NETWORK'),
        platform=PlatformEnum.RARIBLE_V1,
    )

    if order_model is None:
        order_model = await OrderModel.create(
            network=os.getenv('NETWORK'),
            platform=PlatformEnum.RARIBLE_V1,
            internal_order_id=internal_order_id,
            status=OrderStatusEnum.ACTIVE,
            start_at=start_at,
            end_at=end_at,
            salt=order["salt"],
            created_at=datetime.strptime(order["createdAt"], date_pattern),
            last_updated_at=datetime.strptime(order["lastUpdateAt"], date_pattern),
            maker=order["maker"],
            make_asset_class=make.asset_class,
            make_contract=make.contract,
            make_token_id=make.token_id,
            make_value=make.value,
            make_price=take.value / make.value,
            take_asset_class=take.asset_class,
            take_contract=take.contract,
            take_token_id=take.token_id,
            take_value=take.value,
            fill=make.value - AssetValue(order["makeStock"]),
            origin_fees=get_json_parts(origin_fees),
            payouts=get_json_parts(payouts),
        )
    else:
        order_model.last_updated_at = datetime.strptime(order["lastUpdateAt"], date_pattern)
        order_model.make_value = make.value
        order_model.make_price = take.value / make.value
        order_model.take_value = take.value
        order_model.origin_fees = get_json_parts(origin_fees)
        order_model.payouts = get_json_parts(payouts)
        order_model.fill = make.value - AssetValue(order["makeStock"])
        await order_model.save()

    last_order_activity = (
        await ActivityModel.filter(
            network=os.getenv("NETWORK"),
            platform=PlatformEnum.RARIBLE_V1,
            internal_order_id=internal_order_id,
            operation_timestamp=datetime.strptime(order["createdAt"], date_pattern),
        )
        .order_by('-operation_timestamp')
        .first()
    )

    if last_order_activity is None:
        await ActivityModel.create(
            type=ActivityTypeEnum.ORDER_LIST,
            network=os.getenv('NETWORK'),
            platform=PlatformEnum.RARIBLE_V1,
            order_id=order_model.id,
            internal_order_id=internal_order_id,
            maker=order_model.maker,
            make_asset_class=make.asset_class,
            make_contract=make.contract,
            make_token_id=make.token_id,
            make_value=make.value,
            take_asset_class=take.asset_class,
            take_contract=take.contract,
            take_token_id=take.token_id,
            take_value=take.value,
            operation_level=1,
            operation_timestamp=datetime.strptime(order["createdAt"], date_pattern),
            operation_hash=f"o{generate_random_unique_ophash()}",
            operation_counter=int(str(order["salt"])[: 84 - 76]),
            operation_nonce=None,
        )

    legacy_order = await LegacyOrderModel.get_or_none(hash=order["hash"])
    if legacy_order is None:
        await LegacyOrderModel.create(hash=order["hash"], id=order_model.id, data=order)

    if RaribleMetrics.enabled is True:
        RaribleMetrics.set_order_activity(PlatformEnum.RARIBLE_V1, ActivityTypeEnum.ORDER_LIST, 1)


def get_rarible_order_list_activity_kafka_key(activity: RaribleApiOrderListActivity) -> str:
    if isinstance(activity.make, TokenAsset):
        make: TokenAsset = activity.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.take, TokenAsset):
        take: TokenAsset = activity.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_match_activity_kafka_key(activity: RaribleApiOrderMatchActivity) -> str:
    if isinstance(activity.nft, TokenAsset):
        make: TokenAsset = activity.nft
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.payment, TokenAsset):
        take: TokenAsset = activity.payment
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_cancel_activity_kafka_key(activity: RaribleApiOrderCancelActivity) -> str:
    if isinstance(activity.make, TokenAsset):
        make: TokenAsset = activity.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.take, TokenAsset):
        take: TokenAsset = activity.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_kafka_key(order: RaribleApiOrder) -> str:
    assert order
    if isinstance(order.make, TokenAsset):
        make: TokenAsset = order.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(order.take, TokenAsset):
        take: TokenAsset = order.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return order.id


def get_rarible_token_activity_kafka_key(activity: RaribleApiTokenActivity) -> str:
    return f"{activity.contract}:{activity.token_id}"


def get_rarible_collection_activity_kafka_key(activity: RaribleApiCollection) -> str:
    return f"{activity.collection.id}"


def get_rarible_ownership_kafka_key(ownership: RaribleApiOwnership) -> str:
    parts = ownership.ownership_id.split(':')
    return f"{parts[0]}:{parts[1]}"


def get_rarible_token_kafka_key(token: RaribleApiToken) -> str:
    return token.item_id


def get_kafka_key(api_object: AbstractRaribleApiObject) -> str:
    key = api_object.id
    if isinstance(api_object, RaribleApiOrder):
        key = get_rarible_order_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderListActivity):
        key = get_rarible_order_list_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderMatchActivity):
        key = get_rarible_order_match_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderCancelActivity):
        key = get_rarible_order_cancel_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiTokenActivity):
        key = get_rarible_token_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiCollection):
        key = get_rarible_collection_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOwnership):
        key = get_rarible_ownership_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiToken):
        key = get_rarible_token_kafka_key(api_object)
    else:
        key = str(api_object.id)
    return key


async def get_key_for_big_map(ctx: DipDupContext, contract: str, name: str, key: str) -> Response:
    class PayloadSafeSession(requests.Session):
        def send(self, *a, **kw):
            a[0].url = urllib.parse.unquote(a[0].url)
            return requests.Session.send(self, *a, **kw)

    s = PayloadSafeSession()
    return s.get(
        f'{ctx.config.get_tzkt_datasource("tzkt").url}/v1/contracts/{contract}/bigmaps/'
        f'{name}/keys/' + urllib.parse.unquote(key)
    )
