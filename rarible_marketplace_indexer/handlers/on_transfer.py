import logging
from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData
from tortoise.transactions import in_transaction

from rarible_marketplace_indexer.models import TokenTransfer, Token, Ownership


async def on_transfer(
        ctx: HandlerContext,
        token_transfer: TokenTransferData
) -> None:
    logger = logging.getLogger('dipdup.on_transfer')

    # this flag must be false in case of trigger for ownership calculation
    manual_add_ownership = False

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

            is_transfer_to = token_transfer.to_address is not None and token_transfer.to_address not in null_addresses and token_transfer.amount > 0
            if manual_add_ownership and is_transfer_to:
                ownership_to = await Ownership.get_or_none(
                    contract=token_transfer.contract_address,
                    token_id=token_transfer.token_id,
                    owner=token_transfer.to_address
                )

            is_transfer_from = token_transfer.from_address is not None and token_transfer.amount > 0
            if manual_add_ownership and is_transfer_from:
                ownership_from = await Ownership.get_or_none(
                    contract=token_transfer.contract_address,
                    token_id=token_transfer.token_id,
                    owner=token_transfer.from_address
                )

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

                if is_mint:
                    if minted is None:
                        minted = Token(
                            id=token_transfer.tzkt_token_id,
                            contract=token_transfer.contract_address,
                            token_id=token_transfer.token_id,
                            minted_at=token_transfer.timestamp,
                            minted=token_transfer.amount,
                            supply=token_transfer.amount,
                            updated=token_transfer.timestamp
                        )
                    else:
                        minted.minted += token_transfer.amount
                        minted.supply += token_transfer.amount
                        minted.updated = token_transfer.timestamp
                    await minted.save(using_db=connection)

                if is_burn:
                    # burn from null address transfer is possible in the testnet
                    burned = burned or minted

                    burned.supply -= token_transfer.amount
                    burned.deleted = burned.supply <= 0
                    burned.updated = token_transfer.timestamp
                    await burned.save(using_db=connection)

                if manual_add_ownership and is_transfer_to:
                    if ownership_to is None:
                        ownership_to = Ownership(
                            contract=token_transfer.contract_address,
                            token_id=token_transfer.token_id,
                            owner=token_transfer.to_address,
                            balance=token_transfer.amount,
                            updated=token_transfer.timestamp
                        )
                    else:
                        ownership_to.balance += token_transfer.amount
                        ownership_to.updated = token_transfer.timestamp
                    await ownership_to.save(using_db=connection)

                if manual_add_ownership and is_transfer_from and ownership_from is not None:
                    ownership_from.balance -= token_transfer.amount
                    ownership_from.updated = token_transfer.timestamp
                    if ownership_from.balance > 0:
                        await ownership_from.save(using_db=connection)
                    else:
                        await ownership_from.delete(using_db=connection)

            # kafka
            # token_transfer_activity = RaribleApiTokenActivityFactory.build(token_transfer, ctx.datasource)
            # assert token_transfer_activity
            # await producer_send(token_transfer_activity)
