import json
import logging
import os
import random
import string
import uuid
from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional
from uuid import uuid5

import aiohttp
import requests
import warlock as warlock
from base58 import b58encode_check
from dipdup.context import HookContext
from pytezos import MichelsonType
from pytezos import michelson_to_micheline

from rarible_marketplace_indexer.event.dto import MakeDto
from rarible_marketplace_indexer.event.dto import TakeDto
from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import IndexEnum
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
    return f"{ownership.ownership.contract}:{ownership.ownership.token_id}"


def get_rarible_token_kafka_key(token: RaribleApiToken) -> str:
    return f"{token.item.contract}:{token.item.token_id}"


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


collection_metadata_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$ref": "#/definitions/contractMetadataTzip16",
    "definitions": {
        "bignum": {"title": "Big number", "description": "Decimal representation of a big number", "type": "string"},
        "contractMetadataTzip16": {
            "title": "contractMetadataTzip16",
            "description": "Smart Contract Metadata Standard (TZIP-16).",
            "type": "object",
            "properties": {
                "name": {"description": "The identification of the contract.", "type": "string"},
                "description": {
                    "description": "Natural language description of the contract and/or its behavior.",
                    "type": "string",
                },
                "version": {"description": "The version of the contract code.", "type": "string"},
                "license": {
                    "description": "The software license of the contract.",
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "A mnemonic name for the license, see also the License-name case.",
                            "type": "string",
                        },
                        "details": {
                            "description": "Paragraphs of free text, with punctuation and proper language.",
                            "type": "string",
                        },
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
                "authors": {
                    "description": "The list of authors of the contract.",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "homepage": {
                    "description": "A link for humans to follow for documentation, sources, issues, etc.",
                    "type": "string",
                },
                "source": {
                    "description": "Description of how the contract's Michelson was generated.",
                    "type": "object",
                    "properties": {
                        "tools": {
                            "title": "Contract Producing Tools",
                            "description": "List of tools/versions used in producing the Michelson.",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "location": {
                            "title": "Source Location",
                            "description": "Location (URL) of the source code.",
                            "type": "string",
                        },
                    },
                    "additionalProperties": False,
                },
                "interfaces": {
                    "description": "The list of interfaces the contract claims to implement (e.g. TZIP-12).",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "errors": {
                    "description": "Error translators.",
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {
                                "title": "staticErrorTranslator",
                                "description": "A convertor between error codes and expanded messages.",
                                "type": "object",
                                "properties": {
                                    "error": {"$ref": "#/definitions/micheline.tzip-16.expression"},
                                    "expansion": {"$ref": "#/definitions/micheline.tzip-16.expression"},
                                    "languages": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["expansion", "error"],
                                "additionalProperties": False,
                            },
                            {
                                "title": "dynamicErrorTranslator",
                                "description": "An off-chain-view to call to convert error codes to expanded messages.",
                                "type": "object",
                                "properties": {
                                    "view": {"type": "string"},
                                    "languages": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["view"],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
                "views": {
                    "description": "The storage queries, a.k.a. off-chain views provided.",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {
                                "description": "Plain language documentation of the off-chain view; with punctuation.",
                                "type": "string",
                            },
                            "implementations": {
                                "description": "The list of available and equivalent implementations.",
                                "type": "array",
                                "items": {
                                    "oneOf": [
                                        {
                                            "title": "michelsonStorageView",
                                            "description": "An off-chain view using Michelson as a scripting "
                                            "language to interpret the storage of a contract.",
                                            "type": "object",
                                            "properties": {
                                                "michelsonStorageView": {
                                                    "type": "object",
                                                    "properties": {
                                                        "parameter": {
                                                            "description": "The Michelson type of the potential "
                                                            "external parameters required by the "
                                                            "code of the view.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "returnType": {
                                                            "description": "The type of the result of the view, "
                                                            "i.e. the value left on the stack by "
                                                            "the code.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "code": {
                                                            "description": "The Michelson code expression implementing "
                                                            "the view.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "annotations": {
                                                            "description": "List of objects documenting the "
                                                            "annotations used in the 3 above fields.",
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "name": {"type": "string"},
                                                                    "description": {"type": "string"},
                                                                },
                                                                "required": ["description", "name"],
                                                                "additionalProperties": False,
                                                            },
                                                        },
                                                        "version": {
                                                            "description": "A string representing the version of "
                                                            "Michelson that the view is meant to work "
                                                            "with; versions here should be "
                                                            "base58check-encoded protocol hashes.",
                                                            "type": "string",
                                                        },
                                                    },
                                                    "required": ["code", "returnType"],
                                                    "additionalProperties": False,
                                                }
                                            },
                                            "required": ["michelsonStorageView"],
                                            "additionalProperties": False,
                                        },
                                        {
                                            "title": "restApiQueryView",
                                            "description": "An off-chain view using a REST API described in a separate "
                                            "OpenAPI specification. The following parameters form a "
                                            "pointer to the localtion in the OpenAPI description.",
                                            "type": "object",
                                            "properties": {
                                                "restApiQuery": {
                                                    "type": "object",
                                                    "properties": {
                                                        "specificationUri": {
                                                            "description": "A URI pointing at the location of the "
                                                            "OpenAPI specification.",
                                                            "type": "string",
                                                        },
                                                        "baseUri": {
                                                            "description": "The URI-prefix to use to query the API.",
                                                            "type": "string",
                                                        },
                                                        "path": {
                                                            "description": "The path component of the "
                                                            "URI to look-up in "
                                                            "the OpenAPI specification.",
                                                            "type": "string",
                                                        },
                                                        "method": {
                                                            "description": "The HTTP method to use.",
                                                            "type": "string",
                                                            "enum": ["GET", "POST", "PUT"],
                                                        },
                                                    },
                                                    "required": ["path", "specificationUri"],
                                                    "additionalProperties": False,
                                                }
                                            },
                                            "required": ["restApiQuery"],
                                            "additionalProperties": False,
                                        },
                                    ]
                                },
                            },
                            "pure": {"type": "boolean"},
                        },
                        "required": ["implementations", "name"],
                        "additionalProperties": False,
                    },
                },
            },
        },
        "micheline.tzip-16.expression": {
            "oneOf": [
                {
                    "title": "Int",
                    "type": "object",
                    "properties": {"int": {"$ref": "#/definitions/bignum"}},
                    "required": ["int"],
                    "additionalProperties": False,
                },
                {
                    "title": "String",
                    "type": "object",
                    "properties": {"string": {"$ref": "#/definitions/unistring"}},
                    "required": ["string"],
                    "additionalProperties": False,
                },
                {
                    "title": "Bytes",
                    "type": "object",
                    "properties": {"bytes": {"type": "string", "pattern": "^[a-zA-Z0-9]+$"}},
                    "required": ["bytes"],
                    "additionalProperties": False,
                },
                {"title": "Sequence", "type": "array", "items": {"$ref": "#/definitions/micheline.tzip-16.expression"}},
                {
                    "title": "Generic prim (any number of args with or without annot)",
                    "type": "object",
                    "properties": {
                        "prim": {"$ref": "#/definitions/unistring"},
                        "args": {"type": "array", "items": {"$ref": "#/definitions/micheline.tzip-16.expression"}},
                        "annots": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["prim"],
                    "additionalProperties": False,
                },
            ]
        },
        "unistring": {
            "title": "Universal string representation",
            "description": "Either a plain UTF8 string, or a sequence of bytes for strings "
            "that contain invalid byte sequences.",
            "oneOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "properties": {
                        "invalid_utf8_string": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 255},
                        }
                    },
                    "required": ["invalid_utf8_string"],
                    "additionalProperties": False,
                },
            ],
        },
    },
}

token_metadata_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": "#/definitions/asset",
    "title": "Rich Metadata",
    "definitions": {
        "asset": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "description": {
                    "type": "string",
                    "description": "General notes, abstracts, or summaries about the contents of an asset.",
                },
                "minter": {
                    "type": "string",
                    "format": "tzaddress",
                    "description": "The tz address responsible for minting the asset.",
                },
                "creators": {
                    "type": "array",
                    "description": "The primary person, people, or organization(s) responsible for creating the "
                    "intellectual content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "contributors": {
                    "type": "array",
                    "description": "The person, people, or organization(s) that have made substantial creative "
                    "contributions to the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "publishers": {
                    "type": "array",
                    "description": "The person, people, or organization(s) primarily responsible for distributing "
                    "or making the asset available to others in its present form.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "A date associated with the creation or availability of the asset.",
                },
                "blockLevel": {
                    "type": "integer",
                    "description": "Chain block level associated with the creation or availability of the asset.",
                },
                "type": {"type": "string", "description": "A broad definition of the type of content of the asset."},
                "tags": {
                    "type": "array",
                    "description": "A list of tags that describe the subject or content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "genres": {
                    "type": "array",
                    "description": "A list of genres that describe the subject or content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "language": {
                    "type": "string",
                    "format": "https://tools.ietf.org/html/rfc1766",
                    "description": "The language of the intellectual content of the asset as defined in RFC 1776.",
                },
                "identifier": {
                    "type": "string",
                    "description": "A string or number used to uniquely identify the asset. "
                    "Ex. URL, URN, UUID, ISBN, etc.",
                },
                "rights": {"type": "string", "description": "A statement about the asset rights."},
                "rightUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "Links to a statement of rights.",
                },
                "artifactUri": {"type": "string", "format": "uri-reference", "description": "A URI to the asset."},
                "displayUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to an image of the asset. Used for display purposes.",
                },
                "thumbnailUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to an image of the asset for wallets and client applications to "
                    "have a scaled down image to present to end-users. "
                    "Reccomened maximum size of 350x350px.",
                },
                "externalUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI with additional information about the subject or content of the asset.",
                },
                "isTransferable": {
                    "type": "boolean",
                    "description": "All tokens will be transferable by default to allow end-users to send "
                    "them to other end-users. However, this field exists to serve in special cases "
                    "where owners will not be able to transfer the token.",
                },
                "isBooleanAmount": {
                    "type": "boolean",
                    "description": "Describes whether an account can have an amount of exactly 0 or 1. "
                    "(The purpose of this field is for wallets to determine whether or not "
                    "to display balance information and an amount field when transferring.)",
                },
                "shouldPreferSymbol": {
                    "type": "boolean",
                    "description": "Allows wallets to decide whether or not a symbol should be displayed "
                    "in place of a name.",
                },
                "ttl": {
                    "type": "integer",
                    "description": "The maximum amount of time in seconds the asset metadata should be cached.",
                },
                "formats": {"type": "array", "items": {"$ref": "#/definitions/format"}},
                "attributes": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/attribute"},
                    "description": "Custom attributes about the subject or content of the asset.",
                },
                "assets": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/asset"},
                    "description": "Facilitates the description of collections and other types "
                    "of resources that contain multiple assets.",
                },
            },
        },
        "format": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "uri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to the asset represented in this format.",
                },
                "hash": {
                    "type": "string",
                    "description": "A checksum hash of the content of the asset in this format.",
                },
                "mimeType": {"type": "string", "description": "Media (MIME) type of the format."},
                "fileSize": {
                    "type": "integer",
                    "description": "Size in bytes of the content of the asset in this format.",
                },
                "fileName": {
                    "type": "string",
                    "description": "Filename for the asset in this format. For display purposes.",
                },
                "duration": {
                    "type": "string",
                    "format": "time",
                    "description": "Time duration of the content of the asset in this format.",
                },
                "dimensions": {
                    "$ref": "#/definitions/dimensions",
                    "description": "Dimensions of the content of the asset in this format.",
                },
                "dataRate": {
                    "$ref": "#/definitions/dataRate",
                    "description": "Data rate which the content of the asset in this format was captured at.",
                },
            },
        },
        "attribute": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "description": "Name of the attribute."},
                "value": {"type": "string", "description": "Value of the attribute."},
                "type": {"type": "string", "description": "Type of the value. To be used for display purposes."},
            },
            "required": ["name", "value"],
        },
        "dataRate": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"value": {"type": "integer"}, "unit": {"type": "string"}},
            "required": ["unit", "value"],
        },
        "dimensions": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"value": {"type": "string"}, "unit": {"type": "string"}},
            "required": ["unit", "value"],
        },
    },
}

CollectionMetadata = warlock.model_factory(collection_metadata_schema)
TokenMetadata = warlock.model_factory(token_metadata_schema)


def is_collection_metadata_valid(metadata):
    logger = logging.getLogger('metadata')
    if metadata is None:
        return False
    try:
        CollectionMetadata(metadata)
        return True
    except Exception as error:
        logger.warning(f"Invalid metadata for collection {error}: {metadata}")
        return False


def is_token_metadata_valid(metadata):
    logger = logging.getLogger('metadata')
    if metadata is None:
        return False
    try:
        TokenMetadata(metadata)
        return True
    except Exception as error:
        logger.warning(f"Invalid metadata for token {error}: {metadata}")
        return False


async def fetch_metadata(ctx: HookContext, metadata_url: str):
    logger = logging.getLogger('metadata')
    if metadata_url is not None and metadata_url != b'':
        value = metadata_url["value"]
        if type(value) is dict:
            return value
        url = bytes.fromhex(value).decode("utf-8")
        if url.startswith("http"):
            response = requests.get(url)
            if response.ok:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    logger.warning("Could not parse metadata, received invalid content")
                    return None
            else:
                logger.warning(f"Could not parse metadata: {response.status_code} {response.reason}")
                return None
        elif url.startswith("ipfs://ipfs/"):
            ipfs_hash = url.split("ipfs://ipfs/")[1]
            try:
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None
        elif url.startswith("ipfs://"):
            ipfs_hash = url.split("ipfs://")[1]
            try:
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None


async def process_metadata(ctx: HookContext, asset_type: str, asset_id: str):
    try:
        if asset_type is IndexEnum.COLLECTION:
            contract_metadata = await ctx.get_metadata_datasource('metadata').get_contract_metadata(asset_id)
            if contract_metadata is None:
                tzkt = ctx.get_tzkt_datasource("tzkt")
                metadata_url_raw = await tzkt.request(
                    method='get',
                    url=f'v1/contracts/{asset_id}/bigmaps/metadata/keys/""',
                )
                contract_metadata = await fetch_metadata(ctx, metadata_url_raw)
            if is_collection_metadata_valid(contract_metadata):
                return contract_metadata
            else:
                return None
        elif asset_type is IndexEnum.NFT:
            parsed_id = asset_id.split(":")
            if len(parsed_id) != 2:
                raise Exception(f"Invalid Token ID: {asset_id}")
            contract = parsed_id[0]
            token_id = parsed_id[1]
            token_metadata = await ctx.get_metadata_datasource('metadata').get_token_metadata(contract, token_id)
            if token_metadata is None:
                tzkt = ctx.get_tzkt_datasource("tzkt")
                metadata_url_raw = await tzkt.request(
                    method='get',
                    url=f'v1/contracts/{contract}/bigmaps/token_metadata/keys/{token_id}',
                )
                token_metadata = await fetch_metadata(ctx, metadata_url_raw)
            if is_token_metadata_valid(token_metadata):
                return token_metadata
            else:
                return None
    except Exception as ex:
        logging.getLogger("collection_metadata").warning(f"Couldn't process metadata for asset {asset_id}: {ex}")
        return None
