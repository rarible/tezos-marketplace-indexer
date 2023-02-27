import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import Tasks, Collection
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

logger = logging.getLogger("dipdup.reindex_collections")


async def reindex_collections(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    tzkt = ctx.get_tzkt_datasource('tzkt')
    batch = int(ctx.config.hooks.get('reindex_collections').args.get("batch"))
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        current_level = int(task.sample or task.param)
        last_id = 0
        total = 0
        for step in range(batch):
            logger.info(f"Request current_level={current_level}, last_id={last_id}")
            cr_filter = f"&id.gt={last_id}"
            originations = await tzkt.request(
                method='get', url=f"v1/operations/originations?limit=1000&sort.id=asc&level.ge={current_level}{cr_filter}"
            )
            for origination in originations:
                if origination.get("originatedContract") is not None:
                    address = origination['originatedContract']['address']
                    collection = await Collection.get_or_none(id=OriginatedAccountAddress(address))
                    origin_minters = minters(origination)
                    if collection is not None:
                        if collection.minters != origin_minters:
                            collection.minters = origin_minters
                            await collection.save()
                            logger.info(f"Saved minters to {address}")
                current_level = origination['level']
                last_id = origination['id']
            total = len(originations)
            if total == 0:
                break
        if total > 0:
            task.sample = current_level
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


def minters(origination):
    if 'initiator' in origination:
        return [origination['initiator']['address']]
    else:
        return [origination['sender']['address']]
