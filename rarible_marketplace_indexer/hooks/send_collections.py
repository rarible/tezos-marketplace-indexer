import ast
import json
import logging
import traceback

from dipdup.context import HookContext

from rarible_marketplace_indexer.enums import TaskStatus
from rarible_marketplace_indexer.models import Tasks, Collection, CollectionMetadata
from rarible_marketplace_indexer.producer.container import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.collection.factory import RaribleApiCollectionFactory

logger = logging.getLogger("dipdup.send_collections")


async def send_collections(ctx: HookContext, id: int) -> None:
    task = await Tasks.get_or_none(id=id)
    try:
        task.status = TaskStatus.RUNNING
        await task.save()
        continuation = task.sample
        request = Collection.filter(id__lt=continuation) if continuation is not None else Collection.all()
        collections = await request.order_by('-id').limit(1000)
        if len(collections) > 0:
            for collection in collections:
                meta = await CollectionMetadata.get_or_none(id=collection.id)
                metadata = None
                if meta is not None:
                    try:
                        metadata = ast.literal_eval(meta.metadata)
                    except Exception as err:
                        logger.error(f"Unexpected during getting name from meta {err=}, {type(err)=}")
                event = RaribleApiCollectionFactory.build(collection, metadata)
                await producer_send(event)
            task.sample = collections[-1].id
            logger.info(f"Task={task.name} sent {len(collections)} collection, set sample={task.sample}")
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
