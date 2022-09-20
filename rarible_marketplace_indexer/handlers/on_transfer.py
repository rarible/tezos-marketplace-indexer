import logging

from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData

from rarible_marketplace_indexer.models import ActivityTypeEnum, TokenMetadata, Royalties
from rarible_marketplace_indexer.models import Ownership
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenTransfer


async def on_transfer(ctx: HandlerContext, token_transfer: TokenTransferData) -> None:
    logger = logging.getLogger('dipdup.on_transfer')

    if token_transfer.standard == TokenStandard.FA2:
        null_addresses = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]
        transfer = await TokenTransfer.get_or_none(id=token_transfer.id)
        token_id = Token.get_id(token_transfer.contract_address, token_transfer.token_id)
        ownership_id = Ownership.get_id(
            token_transfer.contract_address, token_transfer.token_id, token_transfer.to_address
        )
        if transfer is None:
            is_mint = token_transfer.from_address is None
            minted = None
            burned = None
            if is_mint:
                minted = await Token.get_or_none(id=token_id)
            is_burn = token_transfer.to_address is None or token_transfer.to_address in null_addresses
            if is_burn:
                burned = await Token.get_or_none(id=token_id)
            is_transfer_to = (
                token_transfer.to_address is not None
                and token_transfer.to_address not in null_addresses
                and token_transfer.amount > 0
            )
            if is_transfer_to:
                ownership_to = await Ownership.get_or_none(id=ownership_id)
            is_transfer_from = token_transfer.from_address is not None and token_transfer.amount > 0
            if is_transfer_from:
                ownership_from = await Ownership.get_or_none(id=ownership_id)

            # persist
            if is_mint:
                if minted is None:
                    minted = Token(
                        id=token_id,
                        tzkt_id=token_transfer.tzkt_token_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        minted_at=token_transfer.timestamp,
                        minted=token_transfer.amount,
                        supply=token_transfer.amount,
                        updated=token_transfer.timestamp,
                        metadata_synced=False,
                        metadata_retries=0,
                        royalties_synced=False,
                        royalties_retries=0,
                    )
                    await TokenMetadata.update_or_create(
                        id=token_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        metadata=None,
                    )
                    await Royalties.update_or_create(
                        id=token_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        parts=None,
                    )
                else:
                    minted.minted += token_transfer.amount
                    minted.supply += token_transfer.amount
                    minted.updated = token_transfer.timestamp
                await minted.save()

            if is_burn:

                # We need do it in case mint to burn (it's possible in testnet)
                if burned is not None or minted is not None:
                    burned = burned or minted
                    burned.supply -= token_transfer.amount
                    burned.deleted = burned.supply <= 0
                    burned.updated = token_transfer.timestamp
                    await burned.save()

            if is_transfer_to:
                if ownership_to is None:
                    ownership_to = Ownership(
                        id=ownership_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        owner=token_transfer.to_address,
                        balance=token_transfer.amount,
                        updated=token_transfer.timestamp,
                        created=token_transfer.timestamp,
                    )
                else:
                    ownership_to.balance += token_transfer.amount
                    ownership_to.updated = token_transfer.timestamp
                await ownership_to.save()

            if is_transfer_from and ownership_from is not None:
                ownership_from.balance -= token_transfer.amount
                ownership_from.updated = token_transfer.timestamp
                if ownership_from.balance > 0:
                    await ownership_from.save()
                else:
                    await ownership_from.delete()

            activity_type = ActivityTypeEnum.TOKEN_TRANSFER
            if is_mint:
                activity_type = ActivityTypeEnum.TOKEN_MINT
            if is_burn:
                activity_type = ActivityTypeEnum.TOKEN_BURN
            transaction_id = list(
                filter(
                    bool,
                    [
                        token_transfer.tzkt_transaction_id,
                        token_transfer.tzkt_origination_id,
                        token_transfer.tzkt_migration_id,
                    ],
                )
            ).pop()
            if is_mint and is_burn:
                logger.warning(f"Token {token_transfer.contract_address}:{token_transfer.token_id} was minted to burn")
            else:
                await TokenTransfer(
                    id=token_transfer.id,
                    type=activity_type,
                    date=token_transfer.timestamp,
                    tzkt_token_id=token_transfer.tzkt_token_id,
                    tzkt_transaction_id=transaction_id,
                    contract=token_transfer.contract_address,
                    token_id=token_transfer.token_id,
                    from_address=token_transfer.from_address,
                    to_address=token_transfer.to_address,
                    amount=token_transfer.amount,
                ).save()
