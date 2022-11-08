import logging
import datetime

from dipdup.context import HookContext

from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import TokenTransfer
from rarible_marketplace_indexer.utils.rarible_utils import assert_token_id_length

logger = logging.getLogger("dipdup.import_origination_transfers")


async def import_origination_transfers(ctx: HookContext):
    logger.info('Starting query_origination_transfers')
    null_addresses = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]
    tzkt = ctx.get_tzkt_datasource('tzkt')
    last_id = None
    while True:
        cond = '' if last_id is None else f"&id.gt={last_id}"
        transactions = await tzkt.request(
            method='get',
            url=f"v1/tokens/transfers?originationId.null=false&token.standard=fa2&sort.asc=id"
            f"&select=id,timestamp,token,to,from,amount,originationId{cond}",
        )
        logger.info(f"Got transfers {len(transactions)} for last_id={last_id}")
        for tx in transactions:
            token_transfer = await TokenTransfer.get_or_none(id=tx['id'])

            is_mint = 'from' not in tx or tx['from'] is None
            is_burn = 'to' not in tx or tx['to'] in null_addresses

            activity_type = ActivityTypeEnum.TOKEN_TRANSFER
            contract = tx['token']['contract']['address']
            from_address = None
            to_address = None
            if is_mint:
                activity_type = ActivityTypeEnum.TOKEN_MINT
                to_address = tx['to']['address']
            if is_burn:
                activity_type = ActivityTypeEnum.TOKEN_BURN
                from_address = tx['from']['address']

            if is_mint and is_burn:
                logger.warning(f"Token {contract}:{tx['token']['tokenId']} was minted to burn")
            else:
                if assert_token_id_length(str(tx['token']['id'])):
                    if token_transfer is None:
                        token_transfer = TokenTransfer(id=tx['id'])
                    transaction_id = None
                    if 'transactionId' in tx:
                        transaction_id = tx['transactionId']
                    origination_id = None
                    if 'originationId' in tx:
                        origination_id = tx['originationId']
                    parsed_time = datetime.datetime.strptime(tx['timestamp'], "%Y-%m-%dT%H:%M:%S%z")

                    token_transfer.type = activity_type
                    token_transfer.date = parsed_time
                    token_transfer.tzkt_token_id = tx['token']['id']
                    token_transfer.tzkt_transaction_id = transaction_id
                    token_transfer.tzkt_origination_id = origination_id
                    token_transfer.contract = contract
                    token_transfer.token_id = tx['token']['tokenId']
                    token_transfer.from_address = from_address
                    token_transfer.to_address = to_address
                    token_transfer.amount = int(tx['amount'])

                    await token_transfer.save()
                    logger.info(f'Save transfer with id={token_transfer.id}')

                    # ownerships
                    if to_address is not None:
                        await process(
                            token_transfer.contract, token_transfer.token_id, to_address, token_transfer.date
                        )
                    if from_address is not None:
                        await process(
                            token_transfer.contract, token_transfer.token_id, from_address, token_transfer.date
                        )
                else:
                    logger.warning(
                        f"tokenId is too long, len={len(str(tx['token']['id']))}, transfer id={tx['id']}"
                    )

        if len(transactions) > 0:
            last_id = transactions[-1]['id']
        else:
            break
    logger.info('Finished query_origination_transfers')
