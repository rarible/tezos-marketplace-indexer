import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import TokenTransfer

logger = logging.getLogger("dipdup.process_transaction_hash")


async def process_transaction_hash(ctx: HookContext, iterations, batch):
    logger.info(f'Starting process_transaction_hash [iterations={iterations}, batch={batch}]')
    tzkt = ctx.get_tzkt_datasource('tzkt')

    transfers_without_hash: List[TokenTransfer] = await TokenTransfer.filter(
        hash=None,
        tzkt_transaction_id__isnull=False,
        tzkt_origination_id=None
    ).limit(int(batch) * int(iterations))
    if len(transfers_without_hash) > 0:
        logger.info(f'Found {len(transfers_without_hash)} items without hash, first transfer id: {transfers_without_hash[0].id}')
        chunks = [transfers_without_hash[i:i + int(batch)] for i in range(0, len(transfers_without_hash), int(batch))]
        for chunk in chunks:
            ids = list(set(list(map(lambda item: str(item.tzkt_transaction_id), chunk))))
            tx_map = {}
            for item in chunk:
                tx_map.setdefault(item.tzkt_transaction_id, []).append(item)
            ids_param = ','.join(ids)
            transactions = await tzkt.request(
                method='get', url=f"v1/operations/transactions?id.in={ids_param}&select=id,hash"
            )
            for transaction in transactions:
                for item in tx_map[int(transaction['id'])]:
                    item.hash = transaction['hash']
            await TokenTransfer.bulk_update(chunk, ['hash'])
