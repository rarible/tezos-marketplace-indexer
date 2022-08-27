from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import AbstractAsset
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import TokenAsset


def process_asset(asset: AbstractAsset | None):
    if asset is not None:
        if type(asset) is TokenAsset:
            token_asset: TokenAsset = asset
            if token_asset.asset_type.contract is not None and token_asset.asset_type.token_id is None:
                token_asset.asset_type.token_id = "0"
                return token_asset
    return asset
