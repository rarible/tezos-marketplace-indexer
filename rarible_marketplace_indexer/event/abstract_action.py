import logging
import math
from abc import ABC
from abc import abstractmethod
from datetime import timedelta
from decimal import Decimal
from typing import final

from dipdup.datasources.tzkt.datasource import TzktDatasource
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.dto import CancelDto
from rarible_marketplace_indexer.event.dto import LegacyMatchDto
from rarible_marketplace_indexer.event.dto import ListDto
from rarible_marketplace_indexer.event.dto import MatchDto
from rarible_marketplace_indexer.models import ActivityModel
from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import LegacyOrderModel
from rarible_marketplace_indexer.models import OrderModel
from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.prometheus.rarible_metrics import RaribleMetrics
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.utils.rarible_utils import get_json_parts


class EventInterface(ABC):
    platform: str = NotImplemented

    @classmethod
    @abstractmethod
    async def handle(cls, transaction: Transaction, datasource: TzktDatasource):
        raise NotImplementedError


class AbstractOrderListEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_list_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        logger = logging.getLogger('dipdup.order_list_event')
        dto = cls._get_list_dto(transaction, datasource)
        if not dto.start_at:
            dto.start_at = transaction.data.timestamp

        order = await OrderModel.get_or_none(
            internal_order_id=dto.internal_order_id, network=datasource.network, platform=cls.platform, status=OrderStatusEnum.ACTIVE
        )

        if dto.take.asset_class == AssetClassEnum.FUNGIBLE_TOKEN:
            ft_result = None
            if dto.take.token_id is not None:
                ft_result = await datasource.request(
                    method='get', url=f"v1/tokens?contract={dto.take.contract}&tokenId={dto.take.token_id}"
                )
            else:
                ft_result = await datasource.request(method='get', url=f"v1/tokens?contract={dto.take.contract}")
            # TODO: We need to double-check code below
            if ft_result is not None and "metadata" in ft_result[0]:
                ft = ft_result[0]
                meta = ft["metadata"]
                try:
                    decimals = int(meta["decimals"])
                    dto.take.value = dto.take.value / Decimal(math.pow(10, decimals))
                except Exception:
                    logger.info(f"Failed to get decimals for FT token {dto.take.contract}:{dto.take.token_id} with meta: {meta}")

        if order is None:
            order = await OrderModel.create(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
                start_at=dto.start_at,
                end_at=dto.end_at,
                salt=transaction.data.counter,
                created_at=transaction.data.timestamp,
                last_updated_at=transaction.data.timestamp,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value,
                make_price=dto.take.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value * dto.make.value,
                origin_fees=get_json_parts(dto.origin_fees),
                payouts=get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = get_json_parts(dto.origin_fees)
            order.payouts = get_json_parts(dto.payouts)
            await order.save()

        list_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                operation_hash=transaction.data.hash,
                operation_level=transaction.data.level,
                operation_counter=transaction.data.counter,
                type=ActivityTypeEnum.ORDER_LIST,
            )
            .order_by('-operation_level')
            .first()
        )

        if list_activity is None:
            await ActivityModel.create(
                type=ActivityTypeEnum.ORDER_LIST,
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
                internal_order_id=dto.internal_order_id,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value * dto.make.value,
                operation_level=transaction.data.level,
                operation_timestamp=transaction.data.timestamp,
                operation_hash=transaction.data.hash,
                operation_counter=transaction.data.counter,
                operation_nonce=transaction.data.nonce,
            )

        if RaribleMetrics.enabled is True:
            RaribleMetrics.set_order_activity(cls.platform, ActivityTypeEnum.ORDER_LIST, 1)


class AbstractOrderCancelEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_cancel_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> CancelDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_cancel_dto(transaction, datasource)
        last_order_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )
        if last_order_activity is not None:
            if last_order_activity.type is not ActivityTypeEnum.ORDER_CANCEL:
                cancel_activity = last_order_activity.apply(transaction)

                cancel_activity.type = ActivityTypeEnum.ORDER_CANCEL
                await cancel_activity.save()

        order = (
            await OrderModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
            )
            .order_by('-id')
            .first()
        )

        if order is not None:
            order.status = OrderStatusEnum.CANCELLED
            order.cancelled = True
            order.ended_at = transaction.data.timestamp
            order.last_updated_at = transaction.data.timestamp

            await order.save()

        if RaribleMetrics.enabled is True:
            RaribleMetrics.set_order_activity(cls.platform, ActivityTypeEnum.ORDER_CANCEL, 1)


class AbstractLegacyOrderCancelEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_legacy_cancel_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> CancelDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        logger = logging.getLogger('dipdup.legacy_cancel')

        dto = cls._get_legacy_cancel_dto(transaction, datasource)
        logger.info(f"Legacy order hash = {dto.internal_order_id}")
        legacy_order = (
            await LegacyOrderModel.filter(
                hash=dto.internal_order_id,
            )
            .order_by('-id')
            .first()
        )

        if legacy_order is not None:
            order = (
                await OrderModel.filter(
                    id=legacy_order.id,
                )
                .order_by('-id')
                .first()
            )

            if order is not None:
                order.status = OrderStatusEnum.CANCELLED
                order.cancelled = True
                order.ended_at = transaction.data.timestamp
                order.last_updated_at = transaction.data.timestamp
                await order.save()

                last_order_activity = (
                    await ActivityModel.filter(
                        network=datasource.network, platform=cls.platform, order_id=order.id, type=ActivityTypeEnum.ORDER_CANCEL
                    )
                    .order_by('-operation_timestamp')
                    .first()
                )
                if last_order_activity is not None:
                    cancel_activity = last_order_activity.apply(transaction)

                    cancel_activity.type = ActivityTypeEnum.ORDER_CANCEL
                    await cancel_activity.save()

        if RaribleMetrics.enabled is True:
            RaribleMetrics.set_order_activity(cls.platform, ActivityTypeEnum.ORDER_CANCEL, 1)


class AbstractOrderMatchEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_match_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> MatchDto:
        raise NotImplementedError

    @staticmethod
    @final
    def _process_order_match(order: OrderModel, dto: MatchDto) -> OrderModel:
        order.fill += dto.match_amount

        if order.fill == order.make_value:
            order.status = OrderStatusEnum.FILLED
            order.ended_at = dto.match_timestamp

        return order

    @classmethod
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_match_dto(transaction, datasource)

        last_list_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )

        order = (
            await OrderModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
            )
            .order_by('-id')
            .first()
        )

        if order is not None:
            order.last_updated_at = transaction.data.timestamp
            order = cls._process_order_match(order, dto)
            await order.save()

        if last_list_activity is not None:
            match_activity = last_list_activity.apply(transaction)

            match_activity.type = ActivityTypeEnum.ORDER_MATCH
            match_activity.taker = transaction.data.sender_address

            match_activity.make_value = dto.match_amount
            match_activity.take_value = AssetValue(order.make_price * dto.match_amount)

            await match_activity.save()

        if RaribleMetrics.enabled is True:
            RaribleMetrics.set_order_activity(cls.platform, ActivityTypeEnum.ORDER_MATCH, 1)


class AbstractLegacyOrderMatchEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_legacy_match_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> LegacyMatchDto:
        raise NotImplementedError

    @classmethod
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_legacy_match_dto(transaction, datasource)

        order = (
            await OrderModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-id')
            .first()
        )

        if order is None:
            order = (
                await OrderModel.filter(
                    network=datasource.network,
                    platform=cls.platform,
                    make_asset_class=dto.make.asset_class,
                    make_contract=dto.make.contract,
                    make_token_id=dto.make.token_id,
                    make_value=dto.make.value,
                    take_asset_class=dto.take.asset_class,
                    take_contract=dto.take.contract,
                    take_token_id=dto.take.token_id,
                    take_value=dto.take.value,
                    maker=dto.maker,
                    salt=dto.salt,
                )
                .order_by('-id')
                .first()
            )

        if order is None:
            order = await OrderModel.create(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
                start_at=dto.start,
                end_at=dto.end_at,
                salt=dto.salt,
                created_at=transaction.data.timestamp,
                last_updated_at=transaction.data.timestamp,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value,
                make_price=dto.take.value / dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                origin_fees=get_json_parts(dto.origin_fees),
                payouts=get_json_parts(dto.payouts),
            )
        else:
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.make_price = dto.take.value / dto.make.value
            order.origin_fees = get_json_parts(dto.origin_fees)
            order.payouts = get_json_parts(dto.payouts)

        order.last_updated_at = transaction.data.timestamp

        order.fill += dto.match_amount

        if order.fill == order.make_value:
            order.status = OrderStatusEnum.FILLED
            order.ended_at = dto.match_timestamp

        await order.save()

        last_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
                operation_hash=transaction.data.hash,
                operation_counter=transaction.data.counter,
                operation_nonce=transaction.data.nonce,
            )
            .order_by('-operation_timestamp')
            .first()
        )

        if last_activity is not None:
            match_activity = last_activity.apply(transaction)

            match_activity.type = ActivityTypeEnum.ORDER_MATCH
            match_activity.taker = transaction.data.sender_address

            match_activity.make_value = dto.match_amount
            match_activity.take_value = AssetValue(order.make_price * dto.match_amount)

            last_match = (
                await ActivityModel.filter(
                    network=datasource.network,
                    platform=cls.platform,
                    id=match_activity.id,
                )
                .order_by('-operation_timestamp')
                .first()
            )
            if last_match is None:
                await match_activity.save()
        else:
            await ActivityModel.create(
                type=ActivityTypeEnum.ORDER_MATCH,
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
                internal_order_id=order.internal_order_id,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.match_amount,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=order.make_price * dto.match_amount,
                taker=transaction.data.sender_address,
                operation_level=transaction.data.level,
                operation_timestamp=transaction.data.timestamp,
                operation_hash=transaction.data.hash,
                operation_counter=transaction.data.counter,
                operation_nonce=transaction.data.nonce,
            )

        if RaribleMetrics.enabled is True:
            RaribleMetrics.set_order_activity(cls.platform, ActivityTypeEnum.ORDER_MATCH, 1)


class AbstractPutBidEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_bid_dto(transaction, datasource)

        if dto.end_at is None:
            dto.end_at = dto.start_at + timedelta(weeks=1)

        order = await OrderModel.get_or_none(
            internal_order_id=dto.internal_order_id, network=datasource.network, platform=cls.platform, status=OrderStatusEnum.ACTIVE
        )

        if order is None:
            order = await OrderModel.create(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
                start_at=dto.start_at,
                end_at=dto.end_at,
                salt=transaction.data.counter,
                created_at=transaction.data.timestamp,
                last_updated_at=transaction.data.timestamp,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value * dto.take.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                take_price=dto.make.value,
                origin_fees=get_json_parts(dto.origin_fees),
                payouts=get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = get_json_parts(order.origin_fees) + get_json_parts(dto.origin_fees)
            order.payouts = get_json_parts(order.payouts) + get_json_parts(dto.payouts)
            await order.save()

        await ActivityModel.create(
            type=ActivityTypeEnum.MAKE_BID,
            network=datasource.network,
            platform=cls.platform,
            order_id=order.id,
            internal_order_id=dto.internal_order_id,
            maker=dto.maker,
            make_asset_class=dto.make.asset_class,
            make_contract=dto.make.contract,
            make_token_id=dto.make.token_id,
            make_value=dto.make.value * dto.take.value,
            take_asset_class=dto.take.asset_class,
            take_contract=dto.take.contract,
            take_token_id=dto.take.token_id,
            take_value=dto.take.value,
            operation_level=transaction.data.level,
            operation_timestamp=transaction.data.timestamp,
            operation_hash=transaction.data.hash,
            operation_counter=transaction.data.counter,
            operation_nonce=transaction.data.nonce,
        )


class AbstractPutFloorBidEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_floor_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_floor_bid_dto(transaction, datasource)

        if dto.end_at is None:
            dto.end_at = dto.start_at + timedelta(weeks=1)

        order = await OrderModel.get_or_none(
            internal_order_id=dto.internal_order_id, network=datasource.network, platform=cls.platform, status=OrderStatusEnum.ACTIVE
        )

        if order is None:
            order = await OrderModel.create(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
                start_at=dto.start_at,
                end_at=dto.end_at,
                salt=transaction.data.counter,
                created_at=transaction.data.timestamp,
                last_updated_at=transaction.data.timestamp,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value * dto.take.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                take_price=dto.make.value,
                origin_fees=get_json_parts(dto.origin_fees),
                payouts=get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = get_json_parts(order.origin_fees) + get_json_parts(dto.origin_fees)
            order.payouts = get_json_parts(order.payouts) + get_json_parts(dto.payouts)
            await order.save()

        await ActivityModel.create(
            type=ActivityTypeEnum.MAKE_FLOOR_BID,
            network=datasource.network,
            platform=cls.platform,
            order_id=order.id,
            internal_order_id=dto.internal_order_id,
            maker=dto.maker,
            make_asset_class=dto.make.asset_class,
            make_contract=dto.make.contract,
            make_token_id=dto.make.token_id,
            make_value=dto.make.value,
            take_asset_class=dto.take.asset_class,
            take_contract=dto.take.contract,
            take_token_id=dto.take.token_id,
            take_value=dto.take.value * dto.make.value,
            operation_level=transaction.data.level,
            operation_timestamp=transaction.data.timestamp,
            operation_hash=transaction.data.hash,
            operation_counter=transaction.data.counter,
            operation_nonce=transaction.data.nonce,
        )


class AbstractAcceptBidEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_accept_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> MatchDto:
        raise NotImplementedError

    @staticmethod
    @final
    def _process_bid_match(order: OrderModel, dto: MatchDto) -> OrderModel:
        order.status = OrderStatusEnum.FILLED
        order.ended_at = dto.match_timestamp
        return order

    @classmethod
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_accept_bid_dto(transaction, datasource)

        last_list_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )
        match_activity = last_list_activity.apply(transaction)

        match_activity.type = ActivityTypeEnum.GET_BID
        match_activity.taker = transaction.data.sender_address

        await match_activity.save()

        order = await OrderModel.get(
            network=datasource.network,
            platform=cls.platform,
            internal_order_id=dto.internal_order_id,
            status=OrderStatusEnum.ACTIVE,
        )
        order.last_updated_at = transaction.data.timestamp
        order.taker = transaction.data.sender_address
        order.origin_fees = get_json_parts(order.origin_fees) + get_json_parts(dto.origin_fees)
        order.payouts = get_json_parts(order.payouts) + get_json_parts(dto.payouts)
        order = cls._process_bid_match(order, dto)
        await order.save()


class AbstractAcceptFloorBidEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_accept_floor_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> MatchDto:
        raise NotImplementedError

    @staticmethod
    @final
    def _process_floor_bid_match(order: OrderModel, dto: MatchDto) -> OrderModel:
        order.status = OrderStatusEnum.FILLED
        order.ended_at = dto.match_timestamp
        return order

    @classmethod
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_accept_floor_bid_dto(transaction, datasource)

        last_list_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )
        match_activity = last_list_activity.apply(transaction)

        match_activity.type = ActivityTypeEnum.GET_FLOOR_BID
        match_activity.taker = transaction.data.sender_address

        match_activity.take_token_id = dto.token_id
        await match_activity.save()

        order = await OrderModel.get(
            network=datasource.network,
            platform=cls.platform,
            internal_order_id=dto.internal_order_id,
            status=OrderStatusEnum.ACTIVE,
        )
        order.last_updated_at = transaction.data.timestamp
        order.taker = transaction.data.sender_address
        order.origin_fees = get_json_parts(order.origin_fees) + get_json_parts(dto.origin_fees)
        order.payouts = get_json_parts(order.payouts) + get_json_parts(dto.payouts)
        order = cls._process_floor_bid_match(order, dto)

        await order.save()


class AbstractBidCancelEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_cancel_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> CancelDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_cancel_bid_dto(transaction, datasource)
        last_order_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )
        cancel_activity = last_order_activity.apply(transaction)

        cancel_activity.type = ActivityTypeEnum.CANCEL_BID
        await cancel_activity.save()

        order = (
            await OrderModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
            )
            .order_by('-id')
            .first()
        )

        order.status = OrderStatusEnum.CANCELLED
        order.cancelled = True
        order.ended_at = transaction.data.timestamp
        order.last_updated_at = transaction.data.timestamp

        await order.save()


class AbstractFloorBidCancelEvent(EventInterface):
    @staticmethod
    @abstractmethod
    def _get_cancel_floor_bid_dto(
        transaction: Transaction,
        datasource: TzktDatasource,
    ) -> CancelDto:
        raise NotImplementedError

    @classmethod
    @final
    async def handle(
        cls,
        transaction: Transaction,
        datasource: TzktDatasource,
    ):
        dto = cls._get_cancel_floor_bid_dto(transaction, datasource)
        last_order_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_level')
            .first()
        )
        cancel_activity = last_order_activity.apply(transaction)

        cancel_activity.type = ActivityTypeEnum.ORDER_CANCEL
        await cancel_activity.save()

        order = (
            await OrderModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
                status=OrderStatusEnum.ACTIVE,
            )
            .order_by('-id')
            .first()
        )

        order.status = OrderStatusEnum.CANCELLED
        order.cancelled = True
        order.ended_at = transaction.data.timestamp
        order.last_updated_at = transaction.data.timestamp

        await order.save()
