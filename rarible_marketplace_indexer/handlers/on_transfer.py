import logging
from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData
from tortoise.transactions import in_transaction

from rarible_marketplace_indexer.models import TokenTransfer, Token
from rarible_marketplace_indexer.producer.helper import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.factory import RaribleApiTokenActivityFactory


async def on_transfer(
        ctx: HandlerContext,
        token_transfer: TokenTransferData
) -> None:
    logger = logging.getLogger('dipdup.on_transfer')
    null_addresses = ctx.config.custom['null_addresses']
    if token_transfer.standard == TokenStandard.FA2:
        logger.info(f"get message: ${token_transfer}")
        transfer = await TokenTransfer(
            id=token_transfer.id,
            date=token_transfer.timestamp,
            tzkt_token_id=token_transfer.tzkt_token_id,
            contract=token_transfer.contract_address,
            token_id=token_transfer.token_id,
            from_address=token_transfer.from_address,
            to_address=token_transfer.to_address,
            amount=token_transfer.amount
        )
        async with in_transaction() as connection:
            transfer.save(using_db=connection,update_fields=["date"])
            # logger.info(transfer)
            if token_transfer.from_address is None:
                await Token.update_or_create(
                    tzkt_token_id=token_transfer.tzkt_token_id,
                    contract=token_transfer.contract_address,
                    token_id=token_transfer.token_id,
                    mintedAt=token_transfer.timestamp,
                    supply=token_transfer.amount
                )
        token_transfer_activity = RaribleApiTokenActivityFactory.build(token_transfer, ctx.datasource)
        assert token_transfer_activity
        await producer_send(token_transfer_activity)
