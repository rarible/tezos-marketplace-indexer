from rarible_marketplace_indexer.models import PlatformEnum
from rarible_marketplace_indexer.types.rarible_api_objects.asset.enum import AssetClassEnum
from rarible_marketplace_indexer.types.tezos_objects.tezos_object_hash import OriginatedAccountAddress, \
    ImplicitAccountAddress
from rarible_marketplace_indexer.utils.rarible_utils import RaribleUtils

#correct

internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1hFesk6GV6fT3vak68zz5JxdZ5kK81rvRB"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.XTZ,
            asset=b'',
        )
print(f"correct id = {internal_order_id}")

#wrong
#target 4a472d11a08451438ab9456f7cfe60f2
print("wrong target = 4a472d11a08451438ab9456f7cfe60f2")
wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1hFesk6GV6fT3vak68zz5JxdZ5kK81rvRB"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.XTZ,
            asset=b'00',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1ds2bfUXSULM8c66FfBUe9b6iwXq4JXVBh"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.XTZ,
            asset=b'',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1hFesk6GV6fT3vak68zz5JxdZ5kK81rvRB"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            asset=b'',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1hFesk6GV6fT3vak68zz5JxdZ5kK81rvRB"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            asset=b'00',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1ds2bfUXSULM8c66FfBUe9b6iwXq4JXVBh"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.XTZ,
            asset=b'00',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1ds2bfUXSULM8c66FfBUe9b6iwXq4JXVBh"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.FUNGIBLE_TOKEN,
            asset=b'00',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1ds2bfUXSULM8c66FfBUe9b6iwXq4JXVBh"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.MULTI_TOKEN,
            asset=b'00',
        )
print(f"wrong id = {wrong_internal_order_id}")

wrong_internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=70850,
            seller=ImplicitAccountAddress("tz1ds2bfUXSULM8c66FfBUe9b6iwXq4JXVBh"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=AssetClassEnum.MULTI_TOKEN,
            asset=b'',
        )
print(f"wrong id = {wrong_internal_order_id}")

internal_order_id = RaribleUtils.get_order_hash(
            contract=OriginatedAccountAddress("KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS"),
            token_id=int(70850),
            seller=ImplicitAccountAddress("edpkv8Wo2t5ALJLx8ie3znraLDTk7myLSuPofh55XTmRcphH7wQ4hx"),
            platform=PlatformEnum.RARIBLE_V1,
            asset_class=0,
            asset='b',
        )
print(f"wrong id = {internal_order_id}")