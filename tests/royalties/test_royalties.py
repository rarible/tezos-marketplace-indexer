from contextlib import AsyncExitStack
from os.path import join, dirname
from unittest import IsolatedAsyncioTestCase

from dipdup.config import DipDupConfig, SqliteDatabaseConfig
from dipdup.dipdup import DipDup
from rarible_marketplace_indexer.jobs.royalties import process_royalties

config_path = join(dirname(__file__), 'royalties_config.yml')
config = DipDupConfig.load([config_path])


# class HookContext(DipDupContext):
#     """Execution context of hook callbacks.
#
#     :param hook_config: Configuration of current hook
#     """
#
#     def __init__(
#         self,
#         datasources: Dict[str, Datasource],
#         config: DipDupConfig,
#         callbacks: 'CallbackManager',
#         transactions: TransactionManager,
#         logger: FormattedLogger,
#         hook_config: HookConfig,
#     ) -> None:
#         super().__init__(datasources, config, callbacks, transactions)
#         self.logger = logger
#         self.hook_config = hook_config


async def create_test_dipdup(config: DipDupConfig, stack: AsyncExitStack) -> DipDup:
    config.database = SqliteDatabaseConfig(kind='sqlite', path=':memory:')
    config.initialize(skip_imports=True)

    dipdup = DipDup(config)
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