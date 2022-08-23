from dipdup.datasources.tzkt.datasource import TzktDatasource
from dipdup.models import Transaction

from rarible_marketplace_indexer.event.abstract_action import AbstractOrderListEvent, AbstractOrderCancelEvent, \
    AbstractOrderMatchEvent
from rarible_marketplace_indexer.event.dto import ListDto, MakeDto, TakeDto, CancelDto, MatchDto
from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.teia_v1.parameter.cancel_swap import CancelSwapParameter
from rarible_marketplace_indexer.types.teia_v1.parameter.collect import CollectParameter
from rarible_marketplace_indexer.types.teia_v1.parameter.swap import SwapParameter
from rarible_marketplace_indexer.types.teia_v1.storage import TeiaV1Storage
from rarible_marketplace_indexer.types.tezos_objects.asset_value.asset_value import AssetValue
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress, \
    OriginatedAccountAddress


class TeiaV1OrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.TEIA_V1
    TeiaListTransaction = Transaction[SwapParameter, TeiaV1Storage]

    @staticmethod
    def _get_list_dto(
        transaction: TeiaListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(transaction.parameter.objkt_amount)
        take_value = Xtz.from_u_tezos(transaction.parameter.xtz_per_objkt)

        return ListDto(
            internal_order_id=str(int(transaction.storage.counter) - 1),
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
            origin_fees=[],
            payouts=[],
        )


class TeiaV1OrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.TEIA_V1
    TeiaCancelTransaction = Transaction[CancelSwapParameter, TeiaV1Storage]

    @staticmethod
    def _get_cancel_dto(
        transaction: TeiaCancelTransaction, datasource: TzktDatasource
    ) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class TeiaV1OrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.TEIA_V1
    TeiaMatchTransaction = Transaction[CollectParameter, TeiaV1Storage]

    @staticmethod
    def _get_match_dto(
        transaction: TeiaMatchTransaction, datasource: TzktDatasource
    ) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.__root__,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(1),
            match_timestamp=transaction.data.timestamp,
        )
