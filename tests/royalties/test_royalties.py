from contextlib import AsyncExitStack
from os.path import dirname
from os.path import join
from unittest import IsolatedAsyncioTestCase

from dipdup.config import DipDupConfig
from dipdup.config import SqliteDatabaseConfig
from dipdup.dipdup import DipDup

from rarible_marketplace_indexer.jobs.royalties import process_royalties

config_path = join(dirname(__file__), 'royalties_config.yml')
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


class RoyaltiesTest(IsolatedAsyncioTestCase):
    async def test_royalties_hen(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1RJ6PbjHpwc3M5rw5s2Nbmefwbuwbdxton", "717867")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1ZqdrwVRUs8H1Vts2pFvmR1PLikE8eBVZv", r[0].part_account)
            self.assertEqual("1500", r[0].part_value)

    async def test_royalties_kalamint_public(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1EpGgjQs73QfFJs9z7m1Mxm5MTnpC2tqse", "53057")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1gSCfWiPL8e6us331gtHCvJr9Cuf3jX8g6", r[0].part_account)
            self.assertEqual("1000", r[0].part_value)

    async def test_royalties_kalamint_private(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1RCzrLhBpdKXkyasKGpDTCcdbBTipUk77x", "5492")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1ZLRT3xiBgGRdNrTYXr8Stz4TppT3hukRi", r[0].part_account)
            self.assertEqual("700", r[0].part_value)

    async def test_royalties_fxhash_v1(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE", "522648")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1b8GULAVKS1oHpYLJbwuTKvUegXtRbxH82", r[0].part_account)
            self.assertEqual("1500", r[0].part_value)

    async def test_royalties_fxhash_v2(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1U6EHmNxJTkvaWJ4ThczG4FSDaHC21ssvi", "638313")
            self.assertEqual(2, len(r))
            self.assertEqual("tz1NpUTYsVB2Hdci6ycdWdTz66GvR5oLqQp8", r[0].part_account)
            self.assertEqual("550", r[0].part_value)
            self.assertEqual("tz1g1ZjehDWSJF9aGejq68rph4V24TTqCaRs", r[1].part_account)
            self.assertEqual("550", r[1].part_value)

    async def test_royalties_versum(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1LjmAdYQCLBjwv4S2oFkEzyHVkomAf5MrW", "19471")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1VNAyq17Xpz8QpbxMepbfdrcqNkomeKP35", r[0].part_account)
            self.assertEqual("2500", r[0].part_value)

    async def test_royalties_rarible(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS", "54686")
            self.assertEqual(1, len(r))
            self.assertEqual("tz2G4MMCYStTP9eUU35WQCqMSSJGtjJRZx9g", r[0].part_account)
            self.assertEqual("1000", r[0].part_value)

    async def test_royalties_objkt(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1EffErZNVCPXW2trCMD5gGkACdAbAzj4tT", "0")
            self.assertEqual(1, len(r))
            self.assertEqual("tz2L6ikhCEHz9rZnZWobd7jFSJ6KfkESSP88", r[0].part_account)
            self.assertEqual("1000", r[0].part_value)

    async def test_royalties_objkt_codecrafting(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1PNcZQkJXMQ2Mg92HG1kyrcu3auFX5pfd8", "897")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1SLgrDBpFWjGCnCwyNpCpQC1v8v2N8M2Ks", r[0].part_account)
            self.assertEqual("500", r[0].part_value)

    async def test_royalties_sweet_io(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1QkWhenHZGrRHjrpJMJKYtbJLLy1J6Zk5j", "149")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1e91CZhDWn5v4WAmYojVtKt7ECC5SNtf1c", r[0].part_account)
            self.assertEqual("1000", r[0].part_value)

    async def test_royalties_royalties_manager_with_token_id(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1N4Rrm6BU6229drs6scrH3vard1pPngMyA", "1")
            self.assertEqual(1, len(r))
            self.assertEqual("tz2L6ikhCEHz9rZnZWobd7jFSJ6KfkESSP88", r[0].part_account)
            self.assertEqual("1500", r[0].part_value)

    async def test_royalties_royalties_manager_without_token_id(self) -> None:
        async with AsyncExitStack() as stack:
            dipdup = await create_test_dipdup(config, stack)
            ctx = dipdup._ctx
            r = await process_royalties(ctx, "KT1LRLiZni9vRBUf78bzkKcAxTdchY1k5WjE", "1")
            self.assertEqual(1, len(r))
            self.assertEqual("tz1bJhxQejTtMNLwxf4BcNpYrNmLRcFycShL", r[0].part_account)
            self.assertEqual("500", r[0].part_value)

    # async def test_royalties_embedded_royalties(self) -> None:
    #     async with AsyncExitStack() as stack:
    #         dipdup = await create_test_dipdup(config, stack)
    #         ctx = dipdup._ctx
    #         r = await process_royalties(ctx, "KT1LRLiZni9vRBUf78bzkKcAxTdchY1k5WjE", "1")
    #         self.assertEqual(1, len(r))
    #         self.assertEqual("tz1bJhxQejTtMNLwxf4BcNpYrNmLRcFycShL", r[0].part_account)
    #         self.assertEqual("500", r[0].part_value)
