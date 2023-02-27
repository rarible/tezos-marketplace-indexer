import logging
from datetime import datetime

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Collection
from rarible_marketplace_indexer.models import CollectionMetadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern


logger = logging.getLogger('dipdup.process_collection_events')


async def process_collection_events(
    ctx: HookContext,
    level: int,
) -> None:
    index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION)
    current_level = int(index.last_level) if index is not None else level
    logger.info(f"Processing collections from level {current_level}")

    last_id = 0
    while last_id is not None:
        current_level, last_id, total = await process_originations(ctx, current_level, last_id)
        if index is None:
            await IndexingStatus.create(index=IndexEnum.COLLECTION, last_level=current_level)
        else:
            index.last_level = current_level
            await index.save()
        if total < 1000:
            last_id = None

async def process_originations(ctx, current_level, last_id):
    tzkt = ctx.get_tzkt_datasource('tzkt')
    cr_filter = f"&id.gt={last_id}"
    logger.info(f"Get originations: from {current_level}{cr_filter}")
    originations = await tzkt.request(
        method='get', url=f"v1/operations/originations?limit=1000&sort.id=asc&level.ge={current_level}{cr_filter}"
    )
    for origination in originations:
        if origination.get("originatedContract") is not None:
            if origination["originatedContract"].get("address") is not None:
                contract = await tzkt.request(
                    method='get', url=f"v1/contracts/{origination['originatedContract']['address']}"
                )
                current_level = origination['level']
                last_id = origination['id']
                if "tzips" in contract and 'fa2' in contract['tzips']:
                    if "alias" in contract:
                        origination['alias'] = contract['alias']
                    else:
                        origination['alias'] = ""
                    address = origination['originatedContract']['address']
                    collection = await Collection.get_or_none(id=OriginatedAccountAddress(address))
                    origin_minters = minters(origination)
                    if collection is None:
                        await Collection.create(
                            id=OriginatedAccountAddress(address),
                            owner=ImplicitAccountAddress(origination['sender']['address']),
                            db_updated_at=datetime.now().strftime(date_pattern),
                            name=name(origination),
                            minters=origin_minters,
                            standard='fa2',
                            symbol=None,
                        )
                        collection_metadata = await CollectionMetadata.get_or_none(
                            id=OriginatedAccountAddress(address)
                        )
                        if collection_metadata is None:
                            await CollectionMetadata.create(
                                id=OriginatedAccountAddress(address),
                                metadata=None,
                                metadata_synced=False,
                                metadata_retries=0,
                                db_updated_at=datetime.now().strftime(date_pattern),
                            )
                    else:
                        if collection.minters != origin_minters:
                            collection.minters = origin_minters
                            collection.save()
                            logger.info(f"Saved minters to {address}")
    return current_level, last_id, len(originations)

def minters(origination):
    if 'initiator' in origination:
        return [origination['initiator']['address']]
    else:
        return [origination['sender']['address']]

def name(origination):
    if 'alias' in origination:
        return origination['alias']
    elif 'alias' in origination['contractManager']:
        return origination['contractManager']['alias']
    elif 'alias' in origination['originatedContract']:
        return origination['originatedContract']['alias']
    else:
        return ""
