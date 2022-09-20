from contextlib import AsyncExitStack
from os.path import dirname
from os.path import join
from unittest import IsolatedAsyncioTestCase

from dipdup.config import DipDupConfig
from dipdup.config import SqliteDatabaseConfig
from dipdup.dipdup import DipDup

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum

config_path = join(dirname(__file__), 'metadata_config.yml')
config = DipDupConfig.load([config_path])


async def create_test_dipdup(config: DipDupConfig, stack: AsyncExitStack) -> DipDup:
    config.database = SqliteDatabaseConfig(kind='sqlite', path=':memory:')
    config.initialize()

    dipdup = DipDup(config)
    await dipdup._create_datasources()
    await dipdup._set_up_database(stack)
    await dipdup._set_up_hooks(set())
    await dipdup._initialize_schema()
    await dipdup._set_up_database(stack)
    await dipdup._set_up_transactions(stack)
    await dipdup._set_up_datasources(stack)
    return dipdup


class MetadataTest(IsolatedAsyncioTestCase):
    async def test_token_metadata_dogami(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            token_metadata_dogami = await process_metadata(
                ctx, IndexEnum.NFT, "KT1NVvPsNDChrLRH5K2cy6Sc9r1uuUwdiZQd:100"
            )
            token_metadata_dogami_gap = await process_metadata(
                ctx, IndexEnum.NFT, "KT1CAbPGHUWvkSA9bxMPkqSgabgsjtmRYEda:100"
            )
            self.assertIsNotNone(token_metadata_dogami)
            self.assertIsNotNone(token_metadata_dogami_gap)
            self.assertEqual("Dogami #100", token_metadata_dogami.get("name"))
            self.assertEqual("Varsity Jacket #100", token_metadata_dogami_gap.get("name"))

    async def test_token_metadata_bidou(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            metadata_bidou_8x8 = await process_metadata(ctx, IndexEnum.NFT, "KT1MxDwChiDwd6WBVs24g1NjERUoK622ZEFp:100")
            metadata_bidou_24x24 = await process_metadata(
                ctx, IndexEnum.NFT, "KT1TR1ErEQPTdtaJ7hbvKTJSa1tsGnHGZTpf:100"
            )
            self.assertIsNotNone(metadata_bidou_8x8)
            self.assertIsNotNone(metadata_bidou_24x24)
            self.assertEqual("d097d0b4d0b5d181d18c20d0b820d0a1d0b5d0b9d187d0b0d181", metadata_bidou_8x8.get("name"))
            self.assertEqual("42726f6b656e2e", metadata_bidou_24x24.get("name"))

    async def test_token_metadata_standard(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            metadata = await process_metadata(ctx, IndexEnum.NFT, "KT1RCzrLhBpdKXkyasKGpDTCcdbBTipUk77x:5492")
            self.assertIsNotNone(metadata)
            self.assertEqual("Bear 5492", metadata.get("name"))

    async def test_token_metadata_standard_non_tzkt(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            metadata = await process_metadata(ctx, IndexEnum.NFT, "KT1RvZVDVbZzURnaRmdX2PtbYDVwiuxKQ1tE:51")
            self.assertIsNotNone(metadata)
            self.assertEqual("Basquidoo #048", metadata.get("name"))

    async def test_collection_metadata_rarible_non_standard(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            metadata = await process_metadata(ctx, IndexEnum.COLLECTION, "KT1WiXMmFbrKjSvaKrk5sDN4ACqTLfVKgmv4")
            self.assertIsNotNone(metadata)
            self.assertEqual("Tezy-Bear", metadata.get("name"))

    async def test_collection_metadata_standard(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            metadata_dogami = await process_metadata(ctx, IndexEnum.COLLECTION, "KT1NVvPsNDChrLRH5K2cy6Sc9r1uuUwdiZQd")
            self.assertIsNotNone(metadata_dogami)
            self.assertEqual("DOGAMI", metadata_dogami.get("name"))
