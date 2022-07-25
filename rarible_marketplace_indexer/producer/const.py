import os

ENV = os.getenv('APPLICATION_ENVIRONMENT', 'dev')

class KafkaTopic:
    ORDER_TOPIC: str = f'protocol.{ENV}.tezos.indexer.order'
    ACTIVITY_TOPIC: str = f'protocol.{ENV}.tezos.indexer.activity'
    COLLECTION_TOPIC: str = f'protocol.{ENV}.tezos.indexer.collection'
