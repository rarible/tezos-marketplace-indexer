import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import TokenTransfer

logger = logging.getLogger("transaction_hash")


async def process_transaction_hash(ctx: HookContext, iterations, batch):
    logger.info(f'Starting process_transaction_hash [iterations={iterations}, batch={batch}]')
    tzkt = ctx.get_tzkt_datasource('tzkt')
    for x in range(int(iterations)):
        transfers_without_hash: List[TokenTransfer] = await TokenTransfer.filter(
            hash=None,
            tzkt_transaction_id__not=None,
            tzkt_origination_id=None
        ).limit(int(batch))
        if len(transfers_without_hash) > 0:
            ids = list(map(lambda item: str(item.tzkt_transaction_id), transfers_without_hash))
            tx_map = {x.tzkt_transaction_id: x for x in transfers_without_hash}
            ids_param = ','.join(ids)
            transactions = await tzkt.request(
                method='get', url=f"v1/operations/transactions?id.in={ids_param}&select=id,hash"
            )
            for transaction in transactions:
                tx_map[int(transaction['id'])].hash = transaction['hash']
            await TokenTransfer.bulk_update(transfers_without_hash, ['hash'])
