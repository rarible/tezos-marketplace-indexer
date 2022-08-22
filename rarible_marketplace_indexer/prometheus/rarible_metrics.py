from prometheus_client import Histogram

# Rarible metrics
# Index hit over time (per index)
# total index hit (per index)


_order_activity = Histogram(
    'dipdup_rarible_order_activity',
    'Number of Tezos order activities over time',
    ['index', 'index_type'],
)

_token_activity = Histogram(
    'dipdup_rarible_token_activity',
    'Number of Tezos token activities over time',
    ['index_type', 'contract'],
)




class RaribleMetrics:
    enabled = False

    def __new__(cls):
        raise TypeError('RaribleMetrics is a singleton')

    @classmethod
    def set_order_activity(cls, index: str, index_type: str, value: int) -> None:
        _order_activity.labels(index=index, index_type=index_type).observe(value)

    @classmethod
    def set_token_activity(cls, index_type: str, contract: str, value: int) -> None:
        _token_activity.labels(index_type=index_type, contract=contract).observe(value)
