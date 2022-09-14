import logging

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.producer.helper import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.collection.factory import RaribleApiCollectionFactory


async def process_collection_events(
    ctx: HookContext,
    force_reindex: bool,
    head: int,
) -> None:
    logger = logging.getLogger('dipdup.collection')
    tzkt = ctx.get_tzkt_datasource('tzkt')
    index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION)
    current_level = int(index.last_level) if index is not None else 0

    if current_level == 0 and force_reindex is False:
        current_level = head - 1
    elif force_reindex is True:
        current_level = head
    logger.info(f"Processing originations from level {current_level}")

    last_id = 0
    cr_filter = ""
    while last_id is not None:
        originations = await tzkt.request(
            method='get', url=f"v1/operations/originations?limit=100&level.gt={current_level}{cr_filter}"
        )
        for origination in originations:
            if origination.get("originatedContract") is not None:
                if origination["originatedContract"].get("address") is not None:
                    contract = await tzkt.request(
                        method='get', url=f"v1/contracts/{origination['originatedContract']['address']}"
                    )
                    current_level = origination['level']
                    last_id = origination['id']
                    cr_filter = f"&id.cr={last_id}"
                    if "tzips" in contract and 'fa2' in contract['tzips']:
                        if "alias" in contract:
                            origination['alias'] = contract['alias']
                        else:
                            origination['alias'] = ""
                        logger.info(f"New FA2 originated: {origination['originatedContract']['address']}")
                        collection_event = RaribleApiCollectionFactory.build(origination, tzkt)
                        assert collection_event
                        await producer_send(collection_event)
        if len(originations) < 100:
            last_id = None
    if index is None:
        await IndexingStatus.create(index=IndexEnum.COLLECTION, last_level=head)
    else:
        index.last_level = head
        await index.save()
