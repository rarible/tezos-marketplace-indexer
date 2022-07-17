import logging
import os
import random
import string
from datetime import datetime

import requests
from dipdup.context import HookContext
from pytezos import MichelsonType, michelson_to_micheline

from rarible_marketplace_indexer.event.abstract_action import EventInterface
from rarible_marketplace_indexer.event.dto import MakeDto, TakeDto
from rarible_marketplace_indexer.event.rarible_action import RaribleAware
from rarible_marketplace_indexer.models import IndexingStatus, IndexEnum, OrderModel, PlatformEnum, OrderStatusEnum, \
    LegacyOrderModel, ActivityModel, ActivityTypeEnum
from rarible_marketplace_indexer.producer.container import ProducerContainer
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress, \
    ImplicitAccountAddress

async def on_restart(
    ctx: HookContext,
) -> None:
    logging.getLogger('dipdup').setLevel('INFO')
    logging.getLogger('aiokafka').setLevel('INFO')
    logging.getLogger('db_client').setLevel('INFO')
    await ctx.execute_sql('on_restart')

    ProducerContainer.create_instance(ctx.config.custom, ctx.logger)
    await ProducerContainer.get_instance().start()
    await ctx.fire_hook("import_legacy_orders")



