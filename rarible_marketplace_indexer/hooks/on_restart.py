import logging
import os
from threading import Thread

from dipdup.context import HookContext
from prometheus_client.twisted import MetricsResource
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2ListingOrderListEvent
from rarible_marketplace_indexer.producer.container import ProducerContainer
from rarible_marketplace_indexer.prometheus.rarible_metrics import RaribleMetrics


async def on_restart(
    ctx: HookContext,
) -> None:
    logging.getLogger('dipdup').setLevel('INFO')
    logging.getLogger('aiokafka').setLevel('INFO')
    logging.getLogger('db_client').setLevel('INFO')
    await ctx.execute_sql('on_restart')
    ProducerContainer.create_instance(ctx.config.custom, ctx.logger)
    await ProducerContainer.get_instance().start()

    if ctx.config.prometheus is not None:
        RaribleMetrics.enabled = True
        root = Resource()
        status = Resource()
        root.putChild(b'_status', status)
        status.putChild(b'prometheus', MetricsResource())
        factory = Site(root)
        reactor.listenTCP(8080, factory)
        Thread(target=reactor.run, args=(False,)).start()

    if ctx.config.indexes.get("fxhash_v2_actions") is not None:
        FxhashV2ListingOrderListEvent.fxhash_nft_addresses = {
            "0": ctx.config.custom.get("fxhash_nft_v1"),
            "1": ctx.config.custom.get("fxhash_nft_v2")
        }

    if os.getenv('APPLICATION_ENVIRONMENT') == 'prod' and ctx.config.hooks.get("import_legacy_orders") is not None:
        await ctx.fire_hook("import_legacy_orders")
