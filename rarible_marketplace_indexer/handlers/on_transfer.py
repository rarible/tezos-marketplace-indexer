import logging
from datetime import datetime
import time

import tortoise
from dipdup.context import HandlerContext
from dipdup.enums import TokenStandard
from dipdup.models import TokenTransferData

from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import balance_update_inc
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import Royalties
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata
from rarible_marketplace_indexer.models import TokenTransfer
from rarible_marketplace_indexer.utils.rarible_utils import assert_token_id_length
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern

logger = logging.getLogger('dipdup.on_transfer')
null_addresses = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]


async def on_transfer(ctx: HandlerContext, tf: TokenTransferData) -> None:
    if assert_token_id_length(str(tf.token_id)):
        if tf.standard == TokenStandard.FA2:
            t = time.process_time()
            transfer = await TokenTransfer.get_or_none(id=tf.id)
            token_id = Token.get_id(tf.contract_address, tf.token_id)
            if transfer is None:
                is_mint = tf.from_address is None
                minted = None
                burned = None
                if is_mint:
                    minted = await Token.get_or_none(id=token_id)
                is_burn = tf.to_address is None or tf.to_address in null_addresses
                if is_burn:
                    burned = await Token.get_or_none(id=token_id)

                # persist
                if is_mint:
                    if minted is None:
                        minted = Token(
                            id=token_id,
                            tzkt_id=tf.tzkt_token_id,
                            contract=tf.contract_address,
                            token_id=tf.token_id,
                            minted_at=tf.timestamp,
                            minted=tf.amount,
                            supply=tf.amount,
                            updated=tf.timestamp,
                            db_updated_at=datetime.now().strftime(date_pattern),
                        )
                        token_metadata = await TokenMetadata.get_or_none(id=token_id)
                        if token_metadata is None:
                            try:
                                await TokenMetadata.create(
                                    id=token_id,
                                    contract=tf.contract_address,
                                    token_id=tf.token_id,
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
                                contract=tf.contract_address,
                                token_id=tf.token_id,
                                parts=[],
                                royalties_synced=False,
                                royalties_retries=0,
                                db_updated_at=datetime.now().strftime(date_pattern),
                            )
                    else:
                        minted.minted += tf.amount
                        minted.supply += tf.amount
                        minted.updated = tf.timestamp
                    await minted.save()

                if is_burn:

                    # We need do it in case mint to burn (it's possible in testnet)
                    if burned is not None or minted is not None:
                        burned = burned or minted
                        burned.supply -= tf.amount
                        burned.deleted = burned.supply <= 0
                        burned.updated = tf.timestamp
                        await burned.save()

                activity_type = ActivityTypeEnum.TOKEN_TRANSFER
                if is_mint:
                    activity_type = ActivityTypeEnum.TOKEN_MINT
                if is_burn:
                    activity_type = ActivityTypeEnum.TOKEN_BURN
                if is_mint and is_burn:
                    logger.warning(
                        f"Token {tf.contract_address}:{tf.token_id} was minted to burn"
                    )
                else:
                    await TokenTransfer(
                        id=tf.id,
                        type=activity_type,
                        date=tf.timestamp,
                        tzkt_token_id=tf.tzkt_token_id,
                        tzkt_transaction_id=tf.tzkt_transaction_id,
                        tzkt_origination_id=tf.tzkt_origination_id,
                        contract=tf.contract_address,
                        token_id=tf.token_id,
                        from_address=tf.from_address,
                        to_address=tf.to_address,
                        amount=tf.amount,
                    ).save()

                # incremental balance
                if tf.to_address is not None:
                    await balance_update_inc(tf.contract_address, tf.token_id, tf.to_address, tf.amount, tf.timestamp)
                if tf.from_address is not None:
                    await balance_update_inc(tf.contract_address, tf.token_id, tf.from_address, -tf.amount, tf.timestamp)

            # always recalculate transfers
            # await ownership_transfer(token_transfer)

