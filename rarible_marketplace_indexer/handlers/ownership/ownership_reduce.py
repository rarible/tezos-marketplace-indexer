import logging

from dipdup.models import TokenTransferData
from tortoise import Tortoise

from rarible_marketplace_indexer.models import Ownership

logger = logging.getLogger('dipdup.ownership_reduce')


async def ownership_balance(contract, token_id, owner) -> None:
    conn = Tortoise.get_connection("default")
    result = await conn.execute_query(
        """
    select
        sum(case when to_address = $1 then amount
                 when from_address = $1 then -amount
                 else 0
            end)
    from token_transfer where contract = $2
                          and token_id = $3
                          and (to_address = $1 or from_address = $1)
                          -- pg the comparison of NULL with a value will always result in NULL
                          and ((to_address <> from_address) isnull or (to_address <> from_address))
    """,
        [str(owner), str(contract), str(token_id)],
    )
    amount = result[1][0]['sum']
    if amount is not None:
        if amount < 0:
            logger.warning(f"Amount({amount}) mustn't be negative for ownership: {contract}:{token_id}:{owner}")
    return amount


async def process(contract, token_id, owner, timestamp) -> None:
    amount = await ownership_balance(contract, token_id, owner)
    ownership_id = Ownership.get_id(contract, token_id, owner)
    ownership = await Ownership.get_or_none(id=ownership_id)
    if amount != 0:
        if ownership is not None:
            ownership.balance = amount
            ownership.updated = timestamp
        else:
            ownership = Ownership(
                id=ownership_id,
                contract=contract,
                token_id=token_id,
                owner=owner,
                balance=amount,
                updated=timestamp,
                created=timestamp,
            )
        await ownership.save()
    if amount == 0 and ownership is not None:
        await ownership.delete()


async def ownership_transfer(transfer: TokenTransferData) -> None:
    tasks = []
    if transfer.to_address is not None:
        tasks.append(process(transfer.contract_address, transfer.token_id, transfer.to_address, transfer.timestamp))
    if transfer.from_address is not None:
        tasks.append(process(transfer.contract_address, transfer.token_id, transfer.from_address, transfer.timestamp))
    for task in tasks:
        await task
