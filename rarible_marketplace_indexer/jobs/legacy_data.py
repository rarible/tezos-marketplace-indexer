import json
import logging
import os
from datetime import datetime

import requests

from rarible_marketplace_indexer.models import IndexingStatus, IndexEnum, OrderModel, OrderStatusEnum


async def clean_v1_data():
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
            order_model.ended_at = datetime.now()
            order_model.last_updated_at = datetime.now()
            await order_model.save()

            response = requests.post(
                f"{os.getenv('UNION_API')}/v0.1/refresh/item/TEZOS:{order_model.make_contract}:{order_model.make_token_id}/reconcile?full=true")
            if not response.ok:
                logger.info(
                    f"{order_model.make_contract}:{order_model.make_token_id} need reconcile: Error {response.status_code} - {response.reason}")
            else:
                logger.info(f"{order_model.make_contract}:{order_model.make_token_id} synced properly after legacy cancel")
            legacy_cleaning.last_level = f"{i}"
            await legacy_cleaning.save()

            i = i + 1
        logger.info(f"Cleaned {i} orders")
        legacy_cleaning.last_level = "DONE"
        await legacy_cleaning.save()
