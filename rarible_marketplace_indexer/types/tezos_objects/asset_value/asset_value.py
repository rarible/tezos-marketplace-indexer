from typing import Type

from rarible_marketplace_indexer.types.tezos_objects.asset_value.base_value import BaseValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.base_value import BaseValueField


class AssetValue(BaseValue):
    asset_max_digits: int = 300
    asset_precision: int = 100


class AssetValueField(BaseValueField):
    python_class: Type[AssetValue] = AssetValue
