import asyncio
import datetime
import logging
import os

import requests
from dipdup.context import HookContext

from rarible_marketplace_indexer.models import IndexingStatus, IndexEnum, OrderModel, PlatformEnum, OrderStatusEnum, \
    LegacyOrderModel
from rarible_marketplace_indexer.producer.container import ProducerContainer

async def clean_v1_data():
    legacy_cleaning = await IndexingStatus.get_or_none(index=IndexEnum.V1_CLEANING)
    if legacy_cleaning is None:
        logger = logging.getLogger('dipdup.v1_cleaning')
        logger.info("Processing faulty legacy orders...")
        orders = (
            await OrderModel.filter(
                platform=PlatformEnum.RARIBLE_V1,
                status=OrderStatusEnum.ACTIVE
            )
        )
        faulty_orders: [OrderModel] = []
        i = 0
        for order in orders:
            legacy_order = (
                await LegacyOrderModel.filter(
                    id=order.id,
                )
                .order_by('-id')
                .first()
            )
            if legacy_order is None:
                faulty_orders.append(order)
                logger.info(f"{i} - Cancelling order {order.id}")
                order.status = OrderStatusEnum.CANCELLED
                order.cancelled = True
                order.ended_at = datetime.datetime.now()
                order.last_updated_at = datetime.datetime.now()
                await order.save()

                response = requests.post(
                    f"{os.getenv('UNION_API')}/v0.1/refresh/item/TEZOS:{order.make_contract}:{order.make_token_id}/reconcile?full=true")
                if not response.ok:
                    logger.info(
                        f"{order.make_contract}:{order.make_token_id} need reconcile: Error {response.status_code} - {response.reason}")
                else:
                    logger.info(f"{order.make_contract}:{order.make_token_id} synced properly after legacy cancel")

                i = i + 1
        await IndexingStatus.create(index=IndexEnum.V1_CLEANING, last_level="DONE")
        logger.info(f"Cleaned {len(faulty_orders)} orders")

async def on_restart(
    ctx: HookContext,
) -> None:
    logging.getLogger('dipdup').setLevel('INFO')
    logging.getLogger('aiokafka').setLevel('INFO')
    logging.getLogger('db_client').setLevel('INFO')
    await ctx.execute_sql('on_restart')

    ProducerContainer.create_instance(ctx.config.custom, ctx.logger)

    await ProducerContainer.get_instance().start()

    asyncio.ensure_future(clean_v1_data())
    if os.getenv('APPLICATION_ENVIRONMENT') != 'dev':
        await ctx.fire_hook("import_legacy_orders")

