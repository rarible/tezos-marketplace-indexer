import logging

from dipdup.models import TokenTransferData
from tortoise import Tortoise

from rarible_marketplace_indexer.models import Ownership
from rarible_marketplace_indexer.producer.container import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

logger = logging.getLogger('dipdup.ownership_reduce')
NULL_ADDRESSES = [None, "tz1burnburnburnburnburnburnburjAYjjX", "tz1Ke2h7sDdakHJQh8WX4Z372du1KChsksyU"]


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
    else:
        return 0


async def process(contract, token_id, owner, timestamp) -> None:
    amount = await ownership_balance(contract, token_id, owner)
    ownership_id = Ownership.get_id(contract, token_id, owner)
    ownership = await Ownership.get_or_none(id=ownership_id)
    if amount != 0:
        if ownership is not None:
            ownership.balance = amount
            ownership.updated = timestamp

            if owner in NULL_ADDRESSES:
                await ownership.delete()
            else:
                await ownership.save()
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
            if owner in NULL_ADDRESSES:
                # send delete event without saving ownership
                event = RaribleApiOwnershipFactory.build_delete(ownership)
                await producer_send(event)
            else:
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
