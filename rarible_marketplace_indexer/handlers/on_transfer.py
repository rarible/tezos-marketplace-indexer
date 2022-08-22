import logging
from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData

from rarible_marketplace_indexer.models import TokenTransfer, Token, Ownership
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
            is_burn = token_transfer.to_address is None
            is_nonformal_burn = token_transfer.to_address in null_addresses
            is_transfer_to = token_transfer.to_address is not None and token_transfer.to_address not in null_addresses and token_transfer.amount > 0
            is_transfer_from = token_transfer.from_address is not None and token_transfer.amount > 0

            # persist
            await TokenTransfer.create(
                id=token_transfer.id,
                date=token_transfer.timestamp,
                tzkt_token_id=token_transfer.tzkt_token_id,
                tzkt_transaction_id=token_transfer.tzkt_transaction_id,
                contract=token_transfer.contract_address,
                token_id=token_transfer.token_id,
                from_address=token_transfer.from_address,
                to_address=token_transfer.to_address,
                amount=token_transfer.amount
            )

            if is_nonformal_burn:
                burned = await Token.get(id=token_transfer.tzkt_token_id)
                burned.supply -= token_transfer.amount
                burned.deleted = burned.supply <= 0
                burned.updated = token_transfer.timestamp
                await burned.save()

            # kafka
            token_transfer_activity = None
            if is_mint:
                token_transfer_activity = RaribleApiTokenActivityFactory.build_mint_activity(token_transfer, ctx.datasource)
            if is_burn or is_nonformal_burn:
                token_transfer_activity = RaribleApiTokenActivityFactory.build_burn_activity(token_transfer, ctx.datasource)
            if is_transfer_to and is_transfer_from:
                token_transfer_activity = RaribleApiTokenActivityFactory.build_transfer_activity(token_transfer, ctx.datasource)

            # Could be none if amount == 0
            if token_transfer_activity is not None:
                await producer_send(token_transfer_activity)
