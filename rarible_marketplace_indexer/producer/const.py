import os

ENV = os.getenv('APPLICATION_ENVIRONMENT', 'dev')


class KafkaTopic:
    ORDER_TOPIC: str = f'protocol.{ENV}.tezos.indexer.order'
    ACTIVITY_TOPIC: str = f'protocol.{ENV}.tezos.indexer.activity'
    COLLECTION_TOPIC: str = f'protocol.{ENV}.tezos.indexer.collection'
    OWNERSHIP_TOPIC: str = f'protocol.{ENV}.tezos.indexer.ownership'
    ITEM_TOPIC: str = f'protocol.{ENV}.tezos.indexer.item'
    ITEM_META_TOPIC: str = f'protocol.{ENV}.tezos.indexer.item.meta'
