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
    if token_transfer.standard == TokenStandard.FA2:
        null_addresses = ctx.config.custom['null_addresses']

        transfer = await TokenTransfer.get_or_none(id=token_transfer.id)
        if transfer is None:

            is_mint = token_transfer.from_address is None
            if is_mint:
                minted = await Token.get_or_none(id=token_transfer.tzkt_token_id)
            is_burn = token_transfer.to_address is None or token_transfer.to_address in null_addresses
            if is_burn:
                burned = await Token.get_or_none(id=token_transfer.tzkt_token_id)

            # persist
            async with in_transaction() as connection:
                await TokenTransfer(
                    id=token_transfer.id,
                    date=token_transfer.timestamp,
                    tzkt_token_id=token_transfer.tzkt_token_id,
                    contract=token_transfer.contract_address,
                    token_id=token_transfer.token_id,
                    from_address=token_transfer.from_address,
                    to_address=token_transfer.to_address,
                    amount=token_transfer.amount
                ).save(using_db=connection)

                if is_mint and minted is None:
                    minted = Token(
                        id=token_transfer.tzkt_token_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        minted_at=token_transfer.timestamp,
                        minted=token_transfer.amount,
                        supply=token_transfer.amount,
                        updated=token_transfer.timestamp
                    )
                    await minted.save(using_db=connection)

                if is_burn:
                    # burn from null address transfer is possible in the testnet
                    burned = burned or minted

                    burned.supply = burned.supply - token_transfer.amount
                    burned.deleted = burned.supply == 0
                    burned.updated = token_transfer.timestamp
                    await burned.save(using_db=connection)

            # kafka
            # token_transfer_activity = RaribleApiTokenActivityFactory.build(token_transfer, ctx.datasource)
            # assert token_transfer_activity
            # await producer_send(token_transfer_activity)
