import logging
from datetime import datetime

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Collection
from rarible_marketplace_indexer.models import CollectionMetadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import IndexingStatus
from rarible_marketplace_indexer.producer.helper import producer_send
from rarible_marketplace_indexer.types.rarible_api_objects.collection.factory import RaribleApiCollectionFactory
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern


async def process_collection_events(
    ctx: HookContext,
    level: int,
) -> None:
    logger = logging.getLogger('dipdup.collection')
    tzkt = ctx.get_tzkt_datasource('tzkt')
    index = await IndexingStatus.get_or_none(index=IndexEnum.COLLECTION)
    current_level = int(index.last_level) if index is not None else level

    logger.info(f"Processing collections from level {current_level}")

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
                        address = origination['originatedContract']['address']
                        collection = await Collection.get_or_none(id=OriginatedAccountAddress(address))
                        if collection is None:
                            await Collection.create(
                                id=OriginatedAccountAddress(address),
                                owner=ImplicitAccountAddress(origination['sender']['address']),
                                db_updated_at=datetime.now().strftime(date_pattern),
                                name=origination['alias'],
                                minters=[],
                                standard='fa2',
                                symbol=None,
                            )
                            collection_metadata = await CollectionMetadata.get_or_none(
                                id=OriginatedAccountAddress(address))
                            if collection_metadata is None:
                                await CollectionMetadata.create(
                                    id=OriginatedAccountAddress(address),
                                    metadata=None,
                                    metadata_synced=False,
                                    metadata_retries=0,
                                    db_updated_at=datetime.now().strftime(date_pattern)
                                )

                            logger.info(f"Proccessed collection {address}")
        if len(originations) < 100:
            last_id = None
    if index is None:
        await IndexingStatus.create(index=IndexEnum.COLLECTION, last_level=level)
    else:
        index.last_level = level
        await index.save()
