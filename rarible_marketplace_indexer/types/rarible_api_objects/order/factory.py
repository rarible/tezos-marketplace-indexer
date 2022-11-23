from typing import List

from tortoise.fields import JSONField

from rarible_marketplace_indexer.models import Order
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import Asset
from rarible_marketplace_indexer.types.rarible_api_objects.order.order import RaribleApiOrder
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part


class RaribleApiOrderFactory:
    @staticmethod
    def get_parts(json_parts: JSONField) -> List[Part]:
        parts: List[Part] = []
        for part in json_parts:
            parts.append(Part(part_account=part.get("part_account"), part_value=part.get("part_value")))
        return parts

    @staticmethod
    def build(order: Order) -> RaribleApiOrder:
        return RaribleApiOrder(
            id=order.id,
            network=order.network,
            internal_order_id=order.internal_order_id,
            fill=order.fill,
            platform=order.platform,
            status=order.status,
            start_at=order.start_at,
            end_at=order.end_at,
            cancelled=order.cancelled,
            created_at=order.created_at,
            ended_at=order.ended_at,
            last_updated_at=order.last_updated_at,
            maker=order.maker,
            taker=order.taker,
            make=Asset.make_from_model(order),
            take=Asset.take_from_model(order),
            make_price=order.make_price,
            take_price=order.take_price,
            origin_fees=RaribleApiOrderFactory.get_parts(order.origin_fees),
            payouts=RaribleApiOrderFactory.get_parts(order.payouts),
            salt=order.salt,
        )
