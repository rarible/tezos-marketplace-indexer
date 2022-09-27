from dipdup.datasources.tzkt.datasource import TzktDatasource
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.abstract_action import AbstractOrderCancelEvent, AbstractPutBidEvent, \
    AbstractBidCancelEvent, AbstractAcceptBidEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderListEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderMatchEvent
from rarible_marketplace_indexer.event.dto import CancelDto
from rarible_marketplace_indexer.event.dto import ListDto
from rarible_marketplace_indexer.event.dto import MakeDto
from rarible_marketplace_indexer.event.dto import MatchDto
from rarible_marketplace_indexer.event.dto import TakeDto
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.ask import AskParameter
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.bid import BidParameter
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.fulfill_ask import FulfillAskParameter
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.fulfill_bid import FulfillBidParameter
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.retract_ask import RetractAskParameter
from rarible_marketplace_indexer.types.objkt_marketplace.parameter.retract_bid import RetractBidParameter
from rarible_marketplace_indexer.types.objkt_marketplace.storage import ObjktMarketplaceStorage
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


class ObjktV1OrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktListTransaction = Transaction[AskParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_list_dto(
        transaction: ObjktListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(transaction.parameter.amount)
        take_value = Xtz.from_u_tezos(transaction.parameter.price)

        return ListDto(
            internal_order_id=str(int(transaction.storage.ask_id) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.parameter.fa2),
                token_id=int(transaction.parameter.objkt_id),
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=take_value,
            ),
        )


class ObjktV1OrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktCancelTransaction = Transaction[RetractAskParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_cancel_dto(transaction: ObjktCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class ObjktV1OrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktMatchTransaction = Transaction[FulfillAskParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_match_dto(transaction: ObjktMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
            taker=transaction.data.sender_address,
            token_id=None,
        )


class ObjktV1PutBidEvent(AbstractPutBidEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktListTransaction = Transaction[BidParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_bid_dto(
        transaction: ObjktListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = Xtz.from_u_tezos(transaction.data.amount)
        take_value = AssetValue(1)

        return ListDto(
            internal_order_id=str(int(transaction.storage.bid_id) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.parameter.fa2),
                token_id=int(transaction.parameter.objkt_id),
                value=take_value,
            ),
            start_at=transaction.data.timestamp,
            origin_fees=[],
            payouts=[],
        )


class ObjktV1CancelBidEvent(AbstractBidCancelEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktCancelTransaction = Transaction[RetractBidParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_cancel_bid_dto(
        transaction: ObjktCancelTransaction, datasource: TzktDatasource
    ) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class ObjktV1AcceptBidEvent(AbstractAcceptBidEvent):
    platform = PlatformEnum.OBJKT_V1
    ObjktMatchTransaction = Transaction[FulfillBidParameter, ObjktMarketplaceStorage]

    @staticmethod
    def _get_accept_bid_dto(
        transaction: ObjktMatchTransaction, datasource: TzktDatasource
    ) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )
