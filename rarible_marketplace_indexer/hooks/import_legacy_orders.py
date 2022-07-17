import logging
import os
import random
import string
from datetime import datetime

import requests
from dipdup.context import HookContext
from pytezos import MichelsonType, michelson_to_micheline

from rarible_marketplace_indexer.event.abstract_action import EventInterface
from rarible_marketplace_indexer.event.dto import TakeDto, MakeDto
from rarible_marketplace_indexer.event.rarible_action import RaribleAware
from rarible_marketplace_indexer.models import IndexingStatus, IndexEnum, PlatformEnum, ActivityModel, OrderStatusEnum, \
    OrderModel, ActivityTypeEnum, LegacyOrderModel
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress, \
    ImplicitAccountAddress


def generate_random_unique_ophash(size=50, chars=(string.ascii_lowercase + string.ascii_uppercase + string.digits)):
    return ''.join(random.choice(chars) for _ in range(size))


async def import_legacy_orders(
    ctx: HookContext,
) -> None:
    logger = logging.getLogger('dipdup.legacy')

    date_pattern = "%Y-%m-%dT%H:%M:%SZ"
    index = await IndexingStatus.get_or_none(index=IndexEnum.LEGACY_ORDERS)

    continuation = ""

    if index is not None:
        if index.last_level == "SYNCED":
            continuation = None
        else:
            continuation = index.last_level

    while continuation is not None:
        orders = requests.get(
            f"{os.getenv('LEGACY_API')}/v0.1/orders/all?sort=EARLIEST_FIRST&status=ACTIVE&size=1000{continuation}").json()

        continuation_param = orders.get("continuation")
        if continuation_param is not None:
            continuation = f"&continuation={continuation_param}"
        else:
            continuation = None
        logger.info(f"Next continuation: {continuation}")

        for order in orders["orders"]:
            logger.info(f"Importing order: {order}")

            make = MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(order["make"]["assetType"]["contract"]),
                token_id=int(order["make"]["assetType"]["tokenId"]),
                value=AssetValue(order["make"]["value"])
            )

            take_type = AssetClassEnum.XTZ
            asset_type = None
            asset = b""
            asset_object = None
            if order["take"]["assetType"]["assetClass"] == "FA_1_2":
                take_type = AssetClassEnum.FUNGIBLE_TOKEN
                asset_type = MichelsonType.match(
                    michelson_to_micheline(
                        'address'
                    )
                )

                asset_object = (order["take"]["assetType"]["assetClass"]["contract"])
            elif order["take"]["assetType"]["assetClass"] == "FA_2":
                take_type = AssetClassEnum.FUNGIBLE_TOKEN
                asset_type = MichelsonType.match(
                    michelson_to_micheline(
                        'pair address nat'
                    )
                )
                asset_object = (order["take"]["assetType"]["assetClass"]["contract"],
                                order["take"]["assetType"]["assetClass"]["tokenId"])

            if asset_type is not None:
                asset = asset_type.from_python_object(asset_object).pack().hex()

            take_token_id = order["take"]["assetType"].get("tokenId")
            if take_token_id is not None:
                take_token_id = int(order["take"]["assetType"].get("tokenId"))

            take_contract = order["take"]["assetType"].get("contract")
            if take_contract is not None:
                take_contract = OriginatedAccountAddress(order["take"]["assetType"].get("contract"))

            take = TakeDto(
                asset_class=take_type,
                contract=take_contract,
                token_id=take_token_id,
                value=AssetValue(order["take"]["value"])
            )

            internal_order_id = RaribleAware.get_order_hash(
                contract=OriginatedAccountAddress(make.contract),
                token_id=int(make.token_id),
                seller=ImplicitAccountAddress(order["maker"]),
                platform=PlatformEnum.RARIBLE_V1,
                asset_class=take.asset_class,
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
                origin_fees.append(Part(
                    part_account=fee["account"],
                    part_value=fee["value"]
                ))

            for fee in order["data"]["payouts"]:
                payouts.append(Part(
                    part_account=fee["account"],
                    part_value=fee["value"]
                ))

            order_model = await OrderModel.get_or_none(
                internal_order_id=internal_order_id, network=os.getenv('NETWORK'), platform=PlatformEnum.RARIBLE_V1,
                status=OrderStatusEnum.ACTIVE
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
                    take_asset_class=take.asset_class,
                    take_contract=take.contract,
                    take_token_id=take.token_id,
                    take_value=take.value,
                    fill=order["fill"],
                    origin_fees=EventInterface.get_json_parts(origin_fees),
                    payouts=EventInterface.get_json_parts(payouts),
                )
            else:
                order_model.last_updated_at = datetime.strptime(order["lastUpdateAt"], date_pattern)
                order_model.make_value = make.value
                order_model.take_value = take.value
                order_model.origin_fees = EventInterface.get_json_parts(origin_fees)
                order_model.payouts = EventInterface.get_json_parts(payouts)
                order_model.fill = order["fill"]
                await order_model.save()

            last_order_activity = (
                await ActivityModel.filter(
                    network=os.getenv("NETWORK"),
                    platform=PlatformEnum.RARIBLE_V1,
                    internal_order_id=internal_order_id,
                    operation_timestamp=datetime.strptime(order["createdAt"], date_pattern)
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
                    operation_counter=int(str(order["salt"])[:84 - 76]),
                    operation_nonce=None,
                )

            legacy_order = await LegacyOrderModel.get_or_none(
                hash=order["hash"]
            )
            if legacy_order is None:
                await LegacyOrderModel.create(
                    hash=order["hash"],
                    id=order_model.id,
                    data=order
                )

    if continuation is None:
        continuation = "SYNCED"

    if index is None:
        await IndexingStatus.create(index=IndexEnum.LEGACY_ORDERS, last_level=continuation)
    else:
        index.last_level = continuation
        await index.save()