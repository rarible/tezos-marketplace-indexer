import logging

from dipdup.context import HookContext

logger = logging.getLogger("dipdup.reprocess_tx")


async def reprocess_transactions(ctx: HookContext, index_name: str, contract: str, first_level: int, last_level: int) \
        -> None:
    logger.info(f"Reindexing index {index_name} from level {first_level} to {last_level}")
    await ctx.add_index(
        name='reindex_' + index_name,
        template=index_name + '_template',
        values={
            'contract': contract,
        },
        first_level=first_level,
        last_level=last_level
    )

