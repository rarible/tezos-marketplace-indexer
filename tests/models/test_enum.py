import pytest

from rarible_marketplace_indexer.models import ActivityTypeEnum
from rarible_marketplace_indexer.models import OrderStatusEnum
from rarible_marketplace_indexer.models import PlatformEnum


class TestStrEnum:
    @pytest.mark.parametrize(
        'enum_class, enum_field, enum_value',
        (
            [OrderStatusEnum, OrderStatusEnum.ACTIVE, 'ACTIVE'],
            [OrderStatusEnum, OrderStatusEnum.FILLED, 'FILLED'],
            [OrderStatusEnum, OrderStatusEnum.HISTORICAL, 'HISTORICAL'],
            [OrderStatusEnum, OrderStatusEnum.INACTIVE, 'INACTIVE'],
            [OrderStatusEnum, OrderStatusEnum.CANCELLED, 'CANCELLED'],
            [ActivityTypeEnum, ActivityTypeEnum.ORDER_LIST, 'LIST'],
            [ActivityTypeEnum, ActivityTypeEnum.ORDER_MATCH, 'SELL'],
            [ActivityTypeEnum, ActivityTypeEnum.ORDER_CANCEL, 'CANCEL_LIST'],
            [ActivityTypeEnum, ActivityTypeEnum.TOKEN_MINT, 'MINT'],
            [ActivityTypeEnum, ActivityTypeEnum.TOKEN_TRANSFER, 'TRANSFER'],
            [ActivityTypeEnum, ActivityTypeEnum.TOKEN_BURN, 'BURN'],
            [PlatformEnum, PlatformEnum.HEN, 'HEN'],
            [PlatformEnum, PlatformEnum.OBJKT_V1, 'OBJKT_V1'],
            [PlatformEnum, PlatformEnum.OBJKT_V2, 'OBJKT_V2'],
            [PlatformEnum, PlatformEnum.RARIBLE_V1, 'RARIBLE_V1'],
            [PlatformEnum, PlatformEnum.RARIBLE_V2, 'RARIBLE_V2'],
        ),
    )
    def test_enum(self, enum_class, enum_field, enum_value):
        assert enum_field == enum_value
        assert enum_field.value == enum_value  # noqa
        assert isinstance(enum_field, enum_class)  # noqa
