from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.activity import RaribleApiOrderListActivity, \
    RaribleApiOrderMatchActivity, RaribleApiOrderCancelActivity
from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.activity import RaribleApiTokenActivity
from rarible_marketplace_indexer.types.rarible_api_objects.asset.asset import TokenAsset
from rarible_marketplace_indexer.types.rarible_api_objects.collection.collection import RaribleApiCollection
from rarible_marketplace_indexer.types.rarible_api_objects.order.order import RaribleApiOrder
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.ownership import RaribleApiOwnership
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import RaribleApiToken


def get_rarible_order_list_activity_kafka_key(activity: RaribleApiOrderListActivity) -> str:
    if isinstance(activity.make, TokenAsset):
        make: TokenAsset = activity.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.take, TokenAsset):
        take: TokenAsset = activity.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_match_activity_kafka_key(activity: RaribleApiOrderMatchActivity) -> str:
    if isinstance(activity.nft, TokenAsset):
        make: TokenAsset = activity.nft
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.payment, TokenAsset):
        take: TokenAsset = activity.payment
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_cancel_activity_kafka_key(activity: RaribleApiOrderCancelActivity) -> str:
    if isinstance(activity.make, TokenAsset):
        make: TokenAsset = activity.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(activity.take, TokenAsset):
        take: TokenAsset = activity.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return activity.order_id


def get_rarible_order_kafka_key(order: RaribleApiOrder) -> str:
    assert order
    if isinstance(order.make, TokenAsset):
        make: TokenAsset = order.make
        return f"{make.asset_type.contract}:{make.asset_type.token_id}"
    elif isinstance(order.take, TokenAsset):
        take: TokenAsset = order.take
        return f"{take.asset_type.contract}:{take.asset_type.token_id}"
    else:
        return order.id


def get_rarible_token_activity_kafka_key(activity: RaribleApiTokenActivity) -> str:
    return f"{activity.contract}:{activity.token_id}"


def get_rarible_collection_activity_kafka_key(activity: RaribleApiCollection) -> str:
    return f"{activity.collection['id']}"


def get_rarible_ownership_kafka_key(ownership: RaribleApiOwnership) -> str:
    parts = ownership.ownership_id.split(':')
    return f"{parts[0]}:{parts[1]}"


def get_rarible_token_kafka_key(token: RaribleApiToken) -> str:
    return token.item_id


def get_kafka_key(api_object: AbstractRaribleApiObject) -> str:
    key = api_object.id
    if isinstance(api_object, RaribleApiOrder):
        key = get_rarible_order_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderListActivity):
        key = get_rarible_order_list_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderMatchActivity):
        key = get_rarible_order_match_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOrderCancelActivity):
        key = get_rarible_order_cancel_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiTokenActivity):
        key = get_rarible_token_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiCollection):
        key = get_rarible_collection_activity_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiOwnership):
        key = get_rarible_ownership_kafka_key(api_object)
    elif isinstance(api_object, RaribleApiToken):
        key = get_rarible_token_kafka_key(api_object)
    else:
        key = str(api_object.id)
    return key

