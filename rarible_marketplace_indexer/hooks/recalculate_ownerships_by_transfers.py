
import logging
import traceback

from dipdup.context import HookContext
from tortoise import Tortoise

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.handlers.ownership.ownership_reduce import process
from rarible_marketplace_indexer.models import Tasks

logger = logging.getLogger("dipdup.recalculate_ownerships_by_transfers")


async def recalculate_ownerships_by_transfers(ctx: HookContext, id: int) -> None:
    conn = Tortoise.get_connection("default")
    task = await Tasks.get_or_none(id=id)
    batch = int(ctx.config.hooks.get('recalculate_ownerships_by_transfers').args.get("batch"))
    try:
        task.status = TaskStatus.RUNNING
        await task.save()

        if task.sample is not None:
            contract, token_id, tx_id = task.sample.split(':')
            result = await conn.execute_query(
                """
            select contract, token_id, id, from_address, to_address, date from token_transfer
            where (contract = $1 and token_id = $2 and id > $3)
                or (contract = $1 and token_id > $2 )
                or (contract > $1)
            order by contract, token_id, id limit $4;
            """,
                [contract, token_id, int(tx_id), int(batch)],
            )
        else:
            result = await conn.execute_query(
                """
            select contract, token_id, id, from_address, to_address, date from token_transfer
            order by contract, token_id, id limit $1;
            """, [int(batch)])

        if result[0] > 0:
            ownerships = dict()
            for tx in result[1]:
                if tx['from_address'] is not None:
                    ownership = f"{tx['contract']}:{tx['token_id']}:{tx['from_address']}"
                    if ownership not in ownerships or ownerships[ownership] < tx['date']:
                        ownerships[ownership] = tx['date']
                if tx['to_address'] is not None:
                    ownership = f"{tx['contract']}:{tx['token_id']}:{tx['to_address']}"
                    if ownership not in ownerships or ownerships[ownership] < tx['date']:
                        ownerships[ownership] = tx['date']
            for key, value in ownerships.items():
                contract, token_id, owner = key.split(':')
                await process(contract, token_id, owner, value)
            task.sample = sample(result[1][-1])  # last item
            logger.info(f"Found {result[0]} tx -> {len(ownerships)} ownerships, sample: {task.sample}")
        else:
            logger.info(f"Task={task.name} finished")
            task.status = TaskStatus.FINISHED
    except Exception as err:
        str = traceback.format_exc()
        task.error = str
        task.status = TaskStatus.FAILED
        logger.error(f"Task={task.name} failed with {err}")
        logger.error(f"Task={task.name} trace: {str}")
    task.version += 1
    await task.save()


def sample(row):
    return f"{row['contract']}:{row['token_id']}:{row['id']}"
