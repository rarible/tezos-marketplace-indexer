import logging

from dipdup.context import HookContext

from rarible_marketplace_indexer.producer.container import ProducerContainer


async def on_restart(
    ctx: HookContext,
) -> None:
    logging.getLogger('dipdup').setLevel('INFO')
    logging.getLogger('aiokafka').setLevel('INFO')
    logging.getLogger('db_client').setLevel('INFO')
    await ctx.execute_sql('on_restart')

    ProducerContainer.create_instance(ctx.config.custom, ctx.logger)
    await ProducerContainer.get_instance().start()
    #await ctx.fire_hook("import_legacy_orders")
