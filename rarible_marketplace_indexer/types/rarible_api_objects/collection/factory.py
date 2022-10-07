import json
from datetime import datetime
import os
import uuid
from uuid import uuid5

from dipdup.datasources.tzkt.datasource import TzktDatasource
from rarible_marketplace_indexer.models import Collection

from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import CollectionEvent
from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import RaribleApiCollection


class RaribleApiCollectionFactory:
    @staticmethod
    def build(event: Collection) -> RaribleApiCollection:
        event_id = uuid5(namespace=uuid.NAMESPACE_OID, name=str(datetime.timestamp(datetime.now())))
        return RaribleApiCollection(
            id=event_id,
            network=os.getenv("NETWORK"),
            event_id=str(event_id),
            collection=event.__dict__.fromkeys(["id", "owner", "name", "minters", "standard", "symbol"]),
        )