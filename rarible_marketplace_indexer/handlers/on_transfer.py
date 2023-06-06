import logging
from datetime import datetime
import time

import tortoise
from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData

from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import ownership_transfer
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import Royalties
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata
from rarible_marketplace_indexer.models import TokenTransfer
from rarible_marketplace_indexer.utils.rarible_utils import assert_token_id_length
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern

logger = logging.getLogger('dipdup.on_transfer')
null_addresses = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]


async def on_transfer(ctx: HandlerContext, token_transfer: TokenTransferData) -> None:
    if assert_token_id_length(str(token_transfer.token_id)):
        if token_transfer.standard == TokenStandard.FA2:
            t = time.process_time()
            transfer = await TokenTransfer.get_or_none(id=token_transfer.id)
            token_id = Token.get_id(token_transfer.contract_address, token_transfer.token_id)
            if transfer is None:
                is_mint = token_transfer.from_address is None
                minted = None
                burned = None
                if is_mint:
                    minted = await Token.get_or_none(id=token_id)
                is_burn = token_transfer.to_address is None or token_transfer.to_address in null_addresses
                if is_burn:
                    burned = await Token.get_or_none(id=token_id)

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
                            db_updated_at=datetime.now().strftime(date_pattern),
                        )
                        token_metadata = await TokenMetadata.get_or_none(id=token_id)
                        if token_metadata is None:
                            try:
                                await TokenMetadata.create(
                                    id=token_id,
                                    contract=token_transfer.contract_address,
                                    token_id=token_transfer.token_id,
                                    metadata=None,
                                    metadata_synced=False,
                                    metadata_retries=0,
                                    db_updated_at=datetime.now().strftime(date_pattern),
                                )
                            except tortoise.exceptions.IntegrityError:
                                logger.debug("Token metadata already exists")
                        royalties = await Royalties.get_or_none(id=token_id)
                        if royalties is None:
                            await Royalties.create(
                                id=token_id,
                                contract=token_transfer.contract_address,
                                token_id=token_transfer.token_id,
                                parts=[],
                                royalties_synced=False,
                                royalties_retries=0,
                                db_updated_at=datetime.now().strftime(date_pattern),
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

                activity_type = ActivityTypeEnum.TOKEN_TRANSFER
                if is_mint:
                    activity_type = ActivityTypeEnum.TOKEN_MINT
                if is_burn:
                    activity_type = ActivityTypeEnum.TOKEN_BURN
                if is_mint and is_burn:
                    logger.warning(
                        f"Token {token_transfer.contract_address}:{token_transfer.token_id} was minted to burn"
                    )
                else:
                    await TokenTransfer(
                        id=token_transfer.id,
                        type=activity_type,
                        date=token_transfer.timestamp,
                        tzkt_token_id=token_transfer.tzkt_token_id,
                        tzkt_transaction_id=token_transfer.tzkt_transaction_id,
                        tzkt_origination_id=token_transfer.tzkt_origination_id,
                        contract=token_transfer.contract_address,
                        token_id=token_transfer.token_id,
                        from_address=token_transfer.from_address,
                        to_address=token_transfer.to_address,
                        amount=token_transfer.amount,
                    ).save()

            # always recalculate transfers
            await ownership_transfer(token_transfer)

            elapsed_time = time.process_time() - t
            logger.info(f"Evaluated for {elapsed_time}s")
