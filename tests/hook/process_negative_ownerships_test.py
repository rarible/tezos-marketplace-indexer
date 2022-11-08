from contextlib import AsyncExitStack
from os.path import dirname
from os.path import join
from unittest import IsolatedAsyncioTestCase

from dipdup.config import DipDupConfig
from dipdup.config import SqliteDatabaseConfig
from dipdup.dipdup import DipDup
from tortoise import connections

from rarible_marketplace_indexer.hooks.process_negative_ownerships import validate_transfers

config_path = join(dirname(__file__), 'rarible_config.yml')
config = DipDupConfig.load([config_path])


async def create_test_dipdup(config: DipDupConfig, stack: AsyncExitStack) -> DipDup:
    config.database = SqliteDatabaseConfig(kind='sqlite', path=':memory:')
    config.initialize()

    dipdup = DipDup(config)
    await dipdup._set_up_database(stack)
    await dipdup._set_up_hooks(set())
    await dipdup._create_datasources()
    con = connections.get('default')
    await con.execute_query('''
        create table token_transfer
        (
            id                  bigint                   not null
                primary key,
            type                varchar(16)              not null,
            tzkt_token_id       bigint                   not null,
            tzkt_transaction_id bigint,
            contract            varchar(36)              not null,
            token_id            varchar(256)             not null,
            from_address        varchar(36),
            to_address          varchar(36),
            amount              numeric(300, 100)        not null,
            hash                varchar(51),
            date                timestamp with time zone not null,
            tzkt_origination_id bigint
        );
    ''')
    await dipdup._set_up_datasources(stack)
    return dipdup


# class MetadataTest(IsolatedAsyncioTestCase):
#     async def test_transfers_to(self) -> None:
#         async with AsyncExitStack() as stack:
#             dipdup = await create_test_dipdup(config, stack)
#             ctx = dipdup._ctx
#             await validate_transfers(ctx, 'KT1U6EHmNxJTkvaWJ4ThczG4FSDaHC21ssvi', '1275752', 'tz1RT94jREafiHzgtmkKbiVnDynriUYEi62D', True)

