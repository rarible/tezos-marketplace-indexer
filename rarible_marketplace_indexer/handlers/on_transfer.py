import logging

from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData

from rarible_marketplace_indexer.producer.helper import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.factory import RaribleApiTokenActivityFactory


async def on_transfer(ctx: HandlerContext, token_transfer: TokenTransferData) -> None:
    logger = logging.getLogger('dipdup.on_transfer')
    if token_transfer.standard == TokenStandard.FA2:
        first_level = int(ctx.config.indexes['token_transfers'].first_level)
        if token_transfer.level > first_level:
            token_transfer_activity = RaribleApiTokenActivityFactory.build(token_transfer, ctx.datasource)
            if token_transfer_activity is not None:
                await producer_send(token_transfer_activity)
        else:
            logger.debug(f"Ignore token from level={token_transfer.level}")
