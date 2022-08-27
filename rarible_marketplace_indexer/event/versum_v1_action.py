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
from rarible_marketplace_indexer.types.tezos_objects.asset_value.xtz_value import Xtz
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import ImplicitAccountAddress
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress
from rarible_marketplace_indexer.types.versum_v1.parameter.cancel_swap import CancelSwapParameter
from rarible_marketplace_indexer.types.versum_v1.parameter.collect_swap import CollectSwapParameter
from rarible_marketplace_indexer.types.versum_v1.parameter.create_swap import CreateSwapParameter
from rarible_marketplace_indexer.types.versum_v1.storage import VersumV1Storage


class VersumV1OrderListEvent(AbstractOrderListEvent):
    platform = PlatformEnum.VERSUM_V1
    VersumListTransaction = Transaction[CreateSwapParameter, VersumV1Storage]

    @staticmethod
    def _get_list_dto(
        transaction: VersumListTransaction,
        datasource: TzktDatasource,
    ) -> ListDto:
        make_value = AssetValue(transaction.parameter.token_amount)
        take_value = Xtz.from_u_tezos(transaction.parameter.starting_price_in_nat)

        return ListDto(
            internal_order_id=str(int(transaction.storage.swap_counter) - 1),
            maker=ImplicitAccountAddress(transaction.data.sender_address),
            make=MakeDto(
                asset_class=AssetClassEnum.MULTI_TOKEN,
                contract=OriginatedAccountAddress(transaction.parameter.token.address),
                token_id=int(transaction.parameter.token.nat),
                value=make_value,
            ),
            take=TakeDto(
                asset_class=AssetClassEnum.XTZ,
                contract=None,
                token_id=None,
                value=take_value,
            ),
        )


class VersumV1OrderCancelEvent(AbstractOrderCancelEvent):
    platform = PlatformEnum.VERSUM_V1
    VersumCancelTransaction = Transaction[CancelSwapParameter, VersumV1Storage]

    @staticmethod
    def _get_cancel_dto(transaction: VersumCancelTransaction, datasource: TzktDatasource) -> CancelDto:
        return CancelDto(internal_order_id=transaction.parameter.__root__)


class VersumV1OrderMatchEvent(AbstractOrderMatchEvent):
    platform = PlatformEnum.VERSUM_V1
    VersumMatchTransaction = Transaction[CollectSwapParameter, VersumV1Storage]

    @staticmethod
    def _get_match_dto(transaction: VersumMatchTransaction, datasource: TzktDatasource) -> MatchDto:
        return MatchDto(
            internal_order_id=transaction.parameter.swap_id,
            taker=ImplicitAccountAddress(transaction.data.sender_address),
            token_id=None,
            match_amount=AssetValue(transaction.parameter.amount),
            match_timestamp=transaction.data.timestamp,
        )
