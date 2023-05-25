import json
import logging
import time
import os
from decimal import Decimal
from logging import Logger

from aiokafka import AIOKafkaConsumer
from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Order, Activity

logger: Logger = logging.getLogger('dipdup.consume_ownerships')


async def consume_ownerships(ctx: HookContext):
    config = ctx.config.custom
    env_name = os.getenv('APPLICATION_ENVIRONMENT')
    addresses = config['kafka_address'].split(',')
    logger.info(f"Connecting to internal kafka: {addresses}")
    topic = f'protocol.{env_name}.tezos.indexer.ownership'
    group = f'{env_name}.protocol.tezos.rarible'
    logger.info(f"Listen topic={topic}, group={group}")
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=addresses,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset="earliest",  # If committed offset not found, start from beginning
        group_id=group)
    await consumer.start()
    try:
        async for msg in consumer:
            try:
                t = time.process_time()
                payload = msg.value
                contract, token_id, owner = payload['ownershipId'].split(':')
                orders = await Order.filter(
                    maker=owner,
                    status__in=['ACTIVE', 'INACTIVE'],
                    make_contract=contract,
                    make_token_id=token_id
                    # platform='RARIBLE_V2',
                )
                for order in orders:
                    old_make = order.make_value
                    if payload['type'] == 'DELETE':
                        order.make_value = 0
                    elif payload['type'] == 'UPDATE' and order.status == 'ACTIVE':
                        order.make_value = min(order.make_value, Decimal(payload['ownership']['balance']))
                    elif payload['type'] == 'UPDATE' and order.status == 'INACTIVE':
                        logger.info(f"Reactivate order id={order.id}")
                        activity = await Activity.filter(
                            order_id=order.id,
                            type='LIST'
                        ).order_by('-db_updated_at').first()
                        if activity is not None:
                            order.make_value = min(activity.make_value, Decimal(payload['ownership']['balance']))
                    if order.make_value == 0:
                        order.status = 'INACTIVE'
                    else:
                        order.status = 'ACTIVE'
                    elapsed_time = time.process_time() - t
                    if old_make != order.make_value:
                        logger.info(
                            f"Order id={order.id} ({order.platform}): make_value={old_make}->{order.make_value}, status={order.status}, time={elapsed_time}s")
                        await order.save()
            except Exception as ex:
                logger.error(f"Error while consuming ownership {msg.value}: {ex}")
                raise
    except Exception as ex:
        logger.error(f"Error while consuming ownership {msg.value}: {ex}")
    finally:
        logger.info("Consumer was stopped")
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()
