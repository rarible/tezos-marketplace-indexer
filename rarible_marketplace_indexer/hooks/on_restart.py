import logging
import os
import socketserver
import threading

from dipdup.context import HookContext
from prometheus_client import MetricsHandler

from rarible_marketplace_indexer.event.fxhash_v2_action import FxhashV2ListingOrderListEvent
from rarible_marketplace_indexer.models import IndexingStatus, IndexEnum
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
        prometheus_port = 8080
        metrics_handler = MetricsHandler
        prometheus_httpd = socketserver.TCPServer(("", prometheus_port), metrics_handler)
        prometheus_http_thread = threading.Thread(target=prometheus_httpd.serve_forever)
        prometheus_http_thread.daemon = True
        prometheus_http_thread.start()

    if ctx.config.indexes.get("fxhash_v2_actions") is not None:
        FxhashV2ListingOrderListEvent.fxhash_nft_addresses = {
            "0": ctx.config.custom.get("fxhash_nft_v1"),
            "1": ctx.config.custom.get("fxhash_nft_v2")
        }

    if os.getenv('APPLICATION_ENVIRONMENT') == 'prod' and ctx.config.hooks.get("import_legacy_orders") is not None:
        await ctx.fire_hook("import_legacy_orders")

    if ctx.config.custom.get("token_indexing") is not None:
        token_config = ctx.config.custom.get("token_indexing")
        if token_config["enabled"] == "true":
            if token_config.get("level") is not None:
                await ctx.execute_sql('reset_token_transfers')

    if ctx.config.hooks.get("process_collection_events") is not None:
        index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION)
        if index is None:
            await ctx.fire_hook("process_collection_events", level=0)

