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
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing import ListingParameter
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing_accept import ListingAcceptParameter
from rarible_marketplace_indexer.types.fxhash_v2.parameter.listing_cancel import ListingCancelParameter
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer import OfferParameter
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer_accept import OfferAcceptParameter
from rarible_marketplace_indexer.types.fxhash_v2.parameter.offer_cancel import OfferCancelParameter
from rarible_marketplace_indexer.types.fxhash_v2.storage import FxhashV2Storage
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress

fxhash_nft_addresses = {}


class FxhashV2ListingOrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashListTransaction = Transaction[ListingParameter, FxhashV2Storage]

    @staticmethod
    def _get_list_dto(
        transaction: FxhashListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(1)
        take_value = Xtz.from_u_tezos(transaction.parameter.price)
        return ListDto(
            internal_order_id=str(int(transaction.storage.listings_count) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(fxhash_nft_addresses.get(transaction.parameter.gentk.version)),
                token_id=int(transaction.parameter.gentk.id),
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=take_value,
            ),
        )


class FxhashV2ListingOrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashCancelTransaction = Transaction[ListingCancelParameter, FxhashV2Storage]

    @staticmethod
    def _get_cancel_dto(transaction: FxhashCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class FxhashV2ListingOrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashMatchTransaction = Transaction[ListingAcceptParameter, FxhashV2Storage]

    @staticmethod
    def _get_match_dto(transaction: FxhashMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )


class FxhashV2PutBidEvent(AbstractPutBidEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashListTransaction = Transaction[OfferParameter, FxhashV2Storage]

    @staticmethod
    async def _get_bid_dto(
        transaction: FxhashListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = Xtz.from_u_tezos(transaction.parameter.price)
        take_value = AssetValue(1)

        return ListDto(
            internal_order_id=str(int(transaction.storage.offers_count) - 1),
            start_at=transaction.data.timestamp,
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(fxhash_nft_addresses.get(transaction.parameter.gentk.version)),
                token_id=int(transaction.parameter.gentk.id),
                value=take_value,
            ),
            payouts=[],
        )


class FxhashV2CancelBidEvent(AbstractBidCancelEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashCancelTransaction = Transaction[OfferCancelParameter, FxhashV2Storage]

    @staticmethod
    def _get_cancel_bid_dto(transaction: FxhashCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class FxhashV2AcceptBidEvent(AbstractAcceptBidEvent):
    platform = PlatformEnum.FXHASH_V2
    FxhashMatchTransaction = Transaction[OfferAcceptParameter, FxhashV2Storage]

    @staticmethod
    def _get_accept_bid_dto(transaction: FxhashMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )
