from dipdup.datasources.tzkt.datasource import TzktDatasource
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.abstract_action import AbstractAcceptBidEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractBidCancelEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderCancelEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderListEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderMatchEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractPutBidEvent
from rarible_marketplace_indexer.event.dto import CancelDto
from rarible_marketplace_indexer.event.dto import ListDto
from rarible_marketplace_indexer.event.dto import MakeDto
from rarible_marketplace_indexer.event.dto import MatchDto
from rarible_marketplace_indexer.event.dto import TakeDto
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.ask import AskParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.fulfill_ask import FulfillAskParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.fulfill_offer import FulfillOfferParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.offer import OfferParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.retract_ask import RetractAskParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.parameter.retract_offer import RetractOfferParameter
from rarible_marketplace_indexer.types.objkt_marketplace_v2.storage import ObjktMarketplaceV2Storage
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress


class ObjktV2OrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktListTransaction = Transaction[AskParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_list_dto(
        transaction: ObjktListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(transaction.parameter.editions)
        take_value = Xtz.from_u_tezos(transaction.parameter.amount)

        return ListDto(
            internal_order_id=str(int(transaction.storage.next_ask_id) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.parameter.token.address),
                token_id=int(transaction.parameter.token.token_id),
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=take_value,
            ),
        )


class ObjktV2OrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktCancelTransaction = Transaction[RetractAskParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_cancel_dto(transaction: ObjktCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class ObjktV2OrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktMatchTransaction = Transaction[FulfillAskParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_match_dto(transaction: ObjktMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.ask_id,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
            taker=transaction.data.sender_address,
            token_id=None,
        )


class ObjktV2PutBidEvent(AbstractPutBidEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktListTransaction = Transaction[OfferParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_bid_dto(
        transaction: ObjktListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = Xtz.from_u_tezos(transaction.parameter.amount)
        take_value = AssetValue(1)

        return ListDto(
            internal_order_id=str(int(transaction.storage.next_offer_id) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.parameter.token.address),
                token_id=int(transaction.parameter.token.token_id)
                if transaction.parameter.token.token_id is not None
                else None,
                value=take_value,
            ),
            start_at=transaction.data.timestamp,
            end_at=transaction.parameter.expiry_time,
            origin_fees=[],
            payouts=[],
        )


class ObjktV2CancelBidEvent(AbstractBidCancelEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktCancelTransaction = Transaction[RetractOfferParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_cancel_bid_dto(transaction: ObjktCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class ObjktV2AcceptBidEvent(AbstractAcceptBidEvent):
    platform = PlatformEnum.OBJKT_V2
    ObjktMatchTransaction = Transaction[FulfillOfferParameter, ObjktMarketplaceV2Storage]

    @staticmethod
    def _get_accept_bid_dto(transaction: ObjktMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.offer_id,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=int(transaction.parameter.token_id) if transaction.parameter.token_id is not None else None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )
