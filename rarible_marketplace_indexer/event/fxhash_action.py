from dipdup.datasources.tzkt.datasource import TzktDatasource
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.abstract_action import AbstractOrderCancelEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderListEvent
from rarible_marketplace_indexer.event.abstract_action import AbstractOrderMatchEvent
from rarible_marketplace_indexer.event.dto import CancelDto
from rarible_marketplace_indexer.event.dto import ListDto
from rarible_marketplace_indexer.event.dto import MakeDto
from rarible_marketplace_indexer.event.dto import MatchDto
from rarible_marketplace_indexer.event.dto import TakeDto
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.offer import OfferParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.cancel_offer import CancelOfferParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.parameter.collect import CollectParameter
from rarible_marketplace_indexer.types.fxhash_market_v1.storage import FxhashMarketV1Storage


# V1


class FxhashV1OrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.FXHASH_V1
    FxhashListTransaction = Transaction[OfferParameter, FxhashMarketV1Storage]

    @staticmethod
    def _get_list_dto(
        transaction: FxhashListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(1)
        take_value = AssetValue(transaction.parameter.price)
  
        return ListDto(
            internal_order_id=str(int(transaction.storage.counter) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.storage.objkts),
                token_id=int(transaction.parameter.objkt_id),
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=take_value,
            )
        )


class FxhashV1OrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.FXHASH_V1
    FxhashCancelTransaction = Transaction[CancelOfferParameter, FxhashMarketV1Storage]

    @staticmethod
    def _get_cancel_dto(
        transaction: FxhashCancelTransaction, datasource: TzktDatasource
    ) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class FxhashV1OrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.FXHASH_V1
    FxhashMatchTransaction = Transaction[CollectParameter, FxhashMarketV1Storage]

    @staticmethod
    def _get_match_dto(
        transaction: FxhashMatchTransaction, datasource: TzktDatasource
    ) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )
