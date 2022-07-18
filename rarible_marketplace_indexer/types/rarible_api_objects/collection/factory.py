import uuid
from uuid import uuid5

from dipdup.datasources.tzkt.datasource import TzktDatasource

from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import Collection
from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import RaribleApiCollection


class RaribleApiCollectionFactory:
    @staticmethod
    def build(event: dict, datasource: TzktDatasource) -> RaribleApiCollection:
        return RaribleApiCollection(
            id=uuid5(namespace=uuid.NAMESPACE_OID, name=f"{event['id']}"),
            network=datasource.network,
            event_id=event['id'],
            collection=Collection(
                id=event['originatedContract']['address'],
                owner=event['sender']['address'],
                name=event['alias'],
                minters=[],
                standard='fa2',
                symbol=None,
            ),
        )
