import logging
from datetime import datetime

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import ActivityTypeEnum
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import TokenTransfer, Ownership
from rarible_marketplace_indexer.utils.rarible_utils import assert_token_id_length

logger = logging.getLogger("dipdup.process_negative_ownerships")
NULL_ADDRESSES = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]


async def process_negative_ownerships(ctx: HookContext, batch):
    logger.info(f'Starting process_negative_ownerships')

    ownerships = await Ownership.filter(balance__lt=0).limit(int(batch))
    if len(ownerships) > 0:
        logger.info(f'Found {len(ownerships)} with negative balance')
        try:
            for ownership in ownerships:
                logger.info(f'Processing negative ownership id={ownership.full_id()}')
                dt1 = await validate_transfers(ctx, str(ownership.contract), str(ownership.token_id), str(ownership.owner), True)
                dt2 = await validate_transfers(ctx, str(ownership.contract), str(ownership.token_id), str(ownership.owner), False)
                if dt1 is not None or dt2 is not None:
                    if dt1 is None and dt2 is not None:
                        dt = dt2
                    elif dt1 is not None and dt2 is None:
                        dt = dt1
                    else:
                        dt = max(dt1, dt2)
                    await process(str(ownership.contract), str(ownership.token_id), str(ownership.owner), dt)
            logger.info(f'Finishing processing negative ownerships')
        except Exception as ex:
            logger.error(f'Error during getting transfers for ownership={ownership.full_id()}, {ex}')


async def validate_transfers(ctx: HookContext, contract, token_id, owner, received):
    tzkt = ctx.get_tzkt_datasource('tzkt')
    last_id = None
    direction = 'to' if received else 'from'
    dt = None
    while True:
        cond = '' if last_id is None else f"&id.lt={last_id}"
        request = f"v1/tokens/transfers?token.contract={contract}&token.tokenId={token_id}&{direction}={owner}&sort.desc=id{cond}"
        logger.info(f'Getting transactions from tzkt {request}')
        transactions = await tzkt.request(method='get', url=request)
        for tx in transactions:
            token_transfer = await TokenTransfer.get_or_none(id=tx['id'])
            if token_transfer is None:

                is_mint = 'from' in tx
                is_burn = 'to' not in tx or tx['to'] in NULL_ADDRESSES

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
                        transaction_id = None
                        if 'transactionId' in tx:
                            transaction_id = tx['transactionId']
                        origination_id = None
                        if 'originationId' in tx:
                            origination_id = tx['originationId']
                        token_transfer = await TokenTransfer(
                            id=tx['id'],
                            type=activity_type,
                            date=tx['timestamp'],
                            tzkt_token_id=tx['token']['id'],
                            tzkt_transaction_id=transaction_id,
                            tzkt_origination_id=origination_id,
                            contract=contract,
                            token_id=tx['token']['tokenId'],
                            from_address=from_address,
                            to_address=to_address,
                            amount=int(tx['amount']),
                        )
                        await token_transfer.save()
                        logger.info(f'Save transfer with id={token_transfer.id}')
            if dt is None:
                dt = token_transfer.date
            else:
                dt = max(dt, token_transfer.date)
        if len(transactions) > 0:
            last_id = transactions[-1]['id']
        else:
            break
    return dt