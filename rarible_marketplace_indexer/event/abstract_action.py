from abc import ABC
from abc import abstractmethod
from datetime import timedelta
from typing import List
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
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue


class EventInterface(ABC):
    platform: str = NotImplemented

    @classmethod
    @abstractmethod
    async def handle(cls, transaction: Transaction, datasource: TzktDatasource):
        raise NotImplementedError

    @classmethod
    def get_json_parts(cls, parts: List[Part]):
        json_parts: List[Part] = []
        for part in parts:
            json_parts.append({'part_account': part.part_account, 'part_value': part.part_value})
        return json_parts


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
        dto = cls._get_list_dto(transaction, datasource)
        if not dto.start_at:
            dto.start_at = transaction.data.timestamp

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
                make_value=dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                origin_fees=cls.get_json_parts(dto.origin_fees),
                payouts=cls.get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = cls.get_json_parts(dto.origin_fees)
            order.payouts = cls.get_json_parts(dto.payouts)
            await order.save()

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
            take_value=dto.take.value,
            operation_level=transaction.data.level,
            operation_timestamp=transaction.data.timestamp,
            operation_hash=transaction.data.hash,
            operation_counter=transaction.data.counter,
            operation_nonce=transaction.data.nonce,
        )


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
        dto = cls._get_legacy_cancel_dto(transaction, datasource)
        print(dto.internal_order_id)
        legacy_order = (
            await LegacyOrderModel.filter(
                hash=dto.internal_order_id,
            )
            .order_by('-id')
            .first()
        )

        order = (
            await OrderModel.filter(
                id=legacy_order.id,
            )
            .order_by('-id')
            .first()
        )

        last_order_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
            )
            .order_by('-operation_timestamp')
            .first()
        )

        if order is not None:
            order.status = OrderStatusEnum.CANCELLED
            order.cancelled = True
            order.ended_at = transaction.data.timestamp
            order.last_updated_at = transaction.data.timestamp

            await order.save()

        if last_order_activity is not None:
            cancel_activity = last_order_activity.apply(transaction)

            cancel_activity.type = ActivityTypeEnum.ORDER_CANCEL
            await cancel_activity.save()
        else:
            await ActivityModel.create(
                type=ActivityTypeEnum.ORDER_CANCEL,
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
                internal_order_id=order.internal_order_id,
                maker=order.maker,
                make_asset_class=order.make_asset_class,
                make_contract=order.make_contract,
                make_token_id=order.make_token_id,
                make_value=order.make_value,
                take_asset_class=order.take_asset_class,
                take_contract=order.take_contract,
                take_token_id=order.take_token_id,
                take_value=order.take_value,
                taker=order.taker,
                operation_level=transaction.data.level,
                operation_timestamp=transaction.data.timestamp,
                operation_hash=transaction.data.hash,
                operation_counter=transaction.data.counter,
                operation_nonce=transaction.data.nonce,
            )


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

        order = await OrderModel.get(
            network=datasource.network,
            platform=cls.platform,
            internal_order_id=dto.internal_order_id,
            status=OrderStatusEnum.ACTIVE,
        )

        match_activity = last_list_activity.apply(transaction)

        match_activity.type = ActivityTypeEnum.ORDER_MATCH
        match_activity.taker = transaction.data.sender_address

        match_activity.make_value = dto.match_amount
        match_activity.take_value = AssetValue(order.take_value * dto.match_amount)

        await match_activity.save()

        order.last_updated_at = transaction.data.timestamp
        order = cls._process_order_match(order, dto)

        await order.save()


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
                status=OrderStatusEnum.ACTIVE,
            )
            .order_by('-id')
            .first()
        )

        last_list_activity = (
            await ActivityModel.filter(
                network=datasource.network,
                platform=cls.platform,
                internal_order_id=dto.internal_order_id,
            )
            .order_by('-operation_timestamp')
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
                salt=transaction.data.counter,
                created_at=transaction.data.timestamp,
                last_updated_at=transaction.data.timestamp,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                origin_fees=cls.get_json_parts(dto.origin_fees),
                payouts=cls.get_json_parts(dto.payouts),
            )
        else:
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = cls.get_json_parts(dto.origin_fees)
            order.payouts = cls.get_json_parts(dto.payouts)

        order.last_updated_at = transaction.data.timestamp

        order.fill += dto.match_amount

        if order.fill == order.make_value:
            order.status = OrderStatusEnum.FILLED
            order.ended_at = dto.match_timestamp

        await order.save()

        if last_list_activity is not None:
            match_activity = last_list_activity.apply(transaction)

            match_activity.type = ActivityTypeEnum.ORDER_MATCH
            match_activity.taker = transaction.data.sender_address

            match_activity.make_value = dto.match_amount
            match_activity.take_value = AssetValue(order.take_value * dto.match_amount)

            await match_activity.save()
        else:
            await ActivityModel.create(
                type=ActivityTypeEnum.ORDER_MATCH,
                network=datasource.network,
                platform=cls.platform,
                order_id=order.id,
                internal_order_id=dto.internal_order_id,
                maker=dto.maker,
                make_asset_class=dto.make.asset_class,
                make_contract=dto.make.contract,
                make_token_id=dto.make.token_id,
                make_value=dto.match_amount,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=AssetValue(order.take_value * dto.match_amount),
                taker=transaction.data.sender_address,
                operation_level=transaction.data.level,
                operation_timestamp=transaction.data.timestamp,
                operation_hash=transaction.data.hash,
                operation_counter=transaction.data.counter,
                operation_nonce=transaction.data.nonce,
            )


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
                make_value=dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                origin_fees=cls.get_json_parts(dto.origin_fees),
                payouts=cls.get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = cls.get_json_parts(order.origin_fees) + cls.get_json_parts(dto.origin_fees)
            order.payouts = cls.get_json_parts(order.payouts) + cls.get_json_parts(dto.payouts)
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
            make_value=dto.make.value,
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
                make_value=dto.make.value,
                take_asset_class=dto.take.asset_class,
                take_contract=dto.take.contract,
                take_token_id=dto.take.token_id,
                take_value=dto.take.value,
                origin_fees=cls.get_json_parts(dto.origin_fees),
                payouts=cls.get_json_parts(dto.payouts),
            )
        else:
            order.last_updated_at = transaction.data.timestamp
            order.make_value = dto.make.value
            order.take_value = dto.take.value
            order.origin_fees = cls.get_json_parts(order.origin_fees) + cls.get_json_parts(dto.origin_fees)
            order.payouts = cls.get_json_parts(order.payouts) + cls.get_json_parts(dto.payouts)
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
            take_value=dto.take.value,
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
        order.origin_fees = cls.get_json_parts(order.origin_fees) + cls.get_json_parts(dto.origin_fees)
        order.payouts = cls.get_json_parts(order.payouts) + cls.get_json_parts(dto.payouts)
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
        order.origin_fees = cls.get_json_parts(order.origin_fees) + cls.get_json_parts(dto.origin_fees)
        order.payouts = cls.get_json_parts(order.payouts) + cls.get_json_parts(dto.payouts)
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
