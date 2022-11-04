from typing import List
from typing import Optional
from typing import Type

from aiosignal import Signal
from tortoise import BaseDBAsyncClient
from tortoise.signals import post_delete
from tortoise.signals import post_save

from rarible_marketplace_indexer.models import Activity
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import Collection
from rarible_marketplace_indexer.models import Order
from rarible_marketplace_indexer.models import Ownership
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenTransfer
from rarible_marketplace_indexer.producer.container import ProducerContainer
from rarible_marketplace_indexer.types.rarible_api_objects import AbstractRaribleApiObject
from rarible_marketplace_indexer.utils.rarible_utils import get_kafka_key


async def producer_send(api_object: AbstractRaribleApiObject):
    producer = ProducerContainer.get_instance()
    await producer.send(topic=api_object.kafka_topic, key=get_kafka_key(api_object), value=api_object)


@post_save(Order)
async def signal_order_post_save(
    sender: Order,
    instance: Order,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.order.factory import RaribleApiOrderFactory

    await producer_send(RaribleApiOrderFactory.build(instance))


@post_save(Collection)
async def signal_collection_post_save(
    sender: Collection,
    instance: Collection,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.collection.factory import RaribleApiCollectionFactory

    await producer_send(RaribleApiCollectionFactory.build(instance))


@post_save(Activity)
async def signal_activity_post_save(
    sender: Activity,
    instance: Activity,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.order.factory import (
        RaribleApiOrderActivityFactory,
    )

    await producer_send(RaribleApiOrderActivityFactory.build(instance))


@post_save(TokenTransfer)
async def signal_token_transfer_post_save(
    sender: TokenTransfer,
    instance: TokenTransfer,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.activity.token.factory import (
        RaribleApiTokenActivityFactory,
    )

    if instance.type == ActivityTypeEnum.TOKEN_MINT:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_mint_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_BURN:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_burn_activity(instance)
    if instance.type == ActivityTypeEnum.TOKEN_TRANSFER:
        token_transfer_activity = RaribleApiTokenActivityFactory.build_transfer_activity(instance)
    await producer_send(token_transfer_activity)


@post_save(Ownership)
async def signal_ownership_post_save(
    sender: Ownership,
    instance: Ownership,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    event = RaribleApiOwnershipFactory.build_update(instance)
    await producer_send(event)


@post_delete(Ownership)
async def signal_ownership_post_delete(
    sender: "Type[Signal]", instance: Ownership, using_db: "Optional[BaseDBAsyncClient]"
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.ownership.factory import RaribleApiOwnershipFactory

    event = RaribleApiOwnershipFactory.build_delete(instance)
    await producer_send(event)


@post_save(Token)
async def signal_token_post_save(
    sender: Token,
    instance: Token,
    created: bool,
    using_db: "Optional[BaseDBAsyncClient]",
    update_fields: List[str],
) -> None:
    from rarible_marketplace_indexer.types.rarible_api_objects.token.factory import RaribleApiTokenFactory

    if instance.deleted:
        event = RaribleApiTokenFactory.build_delete(instance)
    else:
        event = RaribleApiTokenFactory.build_update(instance)
    await producer_send(event)
