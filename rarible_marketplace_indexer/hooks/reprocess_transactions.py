import logging

from dipdup.context import HookContext

logger = logging.getLogger("dipdup.reprocess_tx")


async def reprocess_transactions(ctx: HookContext, index_name: str, first_level: int, last_level: int) \
        -> None:
    index_config = ctx.config.indexes.get(index_name)
    await ctx.add_index(
        name=index_name + '_reindex',
        template=index_name + '_template',
        values={
            'contract': index_config.template_values.get("contract"),
        },
    )

