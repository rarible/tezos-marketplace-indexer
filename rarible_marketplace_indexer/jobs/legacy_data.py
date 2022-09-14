import json
import logging
from datetime import datetime

from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.models import OrderModel
from rarible_marketplace_indexer.models import OrderStatusEnum


async def cancel_obsolete_v1_orders():
    legacy_cleaning = await IndexingStatus.get_or_none(index=IndexEnum.V1_CLEANING)
    if legacy_cleaning is None:
        legacy_cleaning = await IndexingStatus.create(index=IndexEnum.V1_CLEANING, last_level="0")

    logger = logging.getLogger('dipdup.v1_cleaning')

    if legacy_cleaning.last_level != "DONE":
        logger.info("Processing faulty legacy orders...")
        data = open("/app/rarible_marketplace_indexer/jobs/data/faulty_legacy_orders.json")
        i = int(legacy_cleaning.last_level)
        orders = json.load(data)
        while i < len(orders):
            order_model = (
                await OrderModel.filter(
                    id=orders[i]["id"],
                )
                .order_by('-id')
                .first()
            )
            logger.info(f"{i} - Cancelling order {order_model.id}")
            order_model.status = OrderStatusEnum.CANCELLED
            order_model.cancelled = True
            order_model.ended_at = datetime.now().replace(microsecond=0)
            order_model.last_updated_at = datetime.now().replace(microsecond=0)
            await order_model.save()
            legacy_cleaning.last_level = f"{i}"
            await legacy_cleaning.save()

            i = i + 1
        logger.info(f"Cleaned {i} orders")
        legacy_cleaning.last_level = "DONE"
        await legacy_cleaning.save()


async def fix_v1_fill_value():
    logger = logging.getLogger('dipdup.v1_cleaning')
    legacy_cleaning = await IndexingStatus.get_or_none(index=IndexEnum.V1_FILL_FIX)
    if legacy_cleaning is None:
        logger.info("Processing incorrect fill value for legacy orders...")
        data = open("/app/rarible_marketplace_indexer/jobs/data/incorrect_fill_v1_orders.json")
        orders = json.load(data)
        for order in orders:
            order_model: OrderModel = (
                await OrderModel.filter(
                    id=order["id"],
                )
                .order_by('-id')
                .first()
            )
            sell_activities: list[ActivityModel] = await ActivityModel.filter(
                order_id=order_model.id, type=ActivityTypeEnum.ORDER_MATCH
            )
            total_sales = 0
            for sell_activity in sell_activities:
                total_sales = total_sales + sell_activity.make_value
            order_model.fill = total_sales
            await order_model.save()
            logger.info(f"Processed order {order_model.id}")
        logger.info("Processed incorrect fill values")
        await IndexingStatus.create(index=IndexEnum.V1_FILL_FIX, last_level="DONE")
