import sys
import uuid
from contextlib import AsyncExitStack
from datetime import datetime
from os.path import dirname
from os.path import join
from unittest import IsolatedAsyncioTestCase
from uuid import uuid5

from dipdup.config import DipDupConfig
from dipdup.config import SqliteDatabaseConfig
from dipdup.dipdup import DipDup

from rarible_marketplace_indexer.hooks.process_token_royalties import process_royalties_for_token
from rarible_marketplace_indexer.models import Royalties, Token, TokenMetadata
from rarible_marketplace_indexer.royalties.royalties import fetch_royalties
from rarible_marketplace_indexer.utils.rarible_utils import date_pattern

config_path = join(dirname(__file__), 'royalties_config.yml')
config = DipDupConfig.load([config_path])

# Before run test it's needed to remove all scripts in the sql/restart directory
async def create_test_dipdup(config: DipDupConfig, stack: AsyncExitStack) -> DipDup:
    config.database = SqliteDatabaseConfig(kind='sqlite', path=':memory:')
    config.initialize()

    dipdup = DipDup(config)
    await dipdup._create_datasources()
    await dipdup._set_up_hooks(set())
    await dipdup._set_up_database(stack)
    await dipdup._set_up_transactions(stack)
    await dipdup._set_up_datasources(stack)
    await dipdup._initialize_schema()
    return dipdup

# We can't run this test on the jenkins due to ipfs requests will be failed
if 'linux' not in sys.platform:
    class RoyaltiesTest(IsolatedAsyncioTestCase):
        async def test_royalties_hen(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1SzbZj7KA5Mddv9q2RESWusVBgirXeA8WN", "56")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1ZqdrwVRUs8H1Vts2pFvmR1PLikE8eBVZv", r[0].part_account)
                self.assertEqual("1500", r[0].part_value)


        async def test_royalties_objkt_full(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx

                contract = "KT1Up463qVJqtW5KF7dQZz5SsWMiS32GtBrw"
                token_id = "1240354"

                oid = f"{contract}:{token_id}"
                id = uuid5(namespace=uuid.NAMESPACE_OID, name=oid)
                await Token.create(
                    id=id,
                    tzkt_id=1,
                    contract=contract,
                    token_id=token_id,
                    minted_at=datetime.now().strftime(date_pattern),
                    minted=1,
                    supply=1,
                    updated=datetime.now().strftime(date_pattern),
                    db_updated_at=datetime.now().strftime(date_pattern),
                )
                # meta = await TokenMetadata.create(
                #     id=id,
                #     contract=contract,
                #     token_id=token_id,
                #     metadata_synced=True,
                #     metadata_retries=0,
                #     db_updated_at=datetime.now().strftime(date_pattern),
                #     metadata="{'royalties': {'decimals': 2, 'shares': {'tz2DWt3yaJA9kuZRnV7cvTWsiXEabpwe6ASA': 10}}, 'name': '65th Annual GRAMMY® Awards NFT', 'description': 'The 65th Annual GRAMMY Awards® NFT is part of the GRAMMYs® genesis NFT collection and gives the holder a chance to win a pair of flyaway tickets to the 2023 65th GRAMMY Awards®. The NFT also includes exclusive access to the GRAMMYs® private Discord channel with additional giveaways, prizes, and exclusive opportunities throughout the year.  This animated NFT is a joyful burst of colors, graphic effects, and tunes to celebrate the collaborative efforts of all music artists, performers, songwriters, producers, engineers, and professionals who make the GRAMMY Awards® possible each year. A portion of the proceeds of the 65th Annual GRAMMY Awards® NFT will go to the Recording Academy’s scholarship fund.  This NFT may unlock OneOf Vault content now or in the future.', 'creators': ['The Recording Academy® x 8th Frame'], 'date': '2022-04-11T13:00', 'tags': ['GREEN'], 'language': 'en', 'artifactUri': 'https://bafybeia4ksjp6coan7lswami3zyfzhkujliyboe2q77r4wlai4ly5yrgru.ipfs.nftstorage.link/', 'formats': [{'uri': 'https://bafybeia4ksjp6coan7lswami3zyfzhkujliyboe2q77r4wlai4ly5yrgru.ipfs.nftstorage.link/', 'mimeType': 'video/mp4', 'fileSize': 10200000, 'duration': '00:00:10', 'dataRate': {'value': 8452, 'unit': 'kbps'}, 'dimensions': {'value': '1080x1080', 'unit': 'px'}}], 'displayUri': 'https://bafybeigsvpfkodmmu5mh6xdyct6i2viz2gkkxh3etndtu372nem5rdtx6m.ipfs.nftstorage.link/', 'thumbnailUri': 'https://bafybeigsvpfkodmmu5mh6xdyct6i2viz2gkkxh3etndtu372nem5rdtx6m.ipfs.nftstorage.link/', 'rightUri': 'https://bafkreignl7v33pqbygymmvmnoabedgiegi5nb2zrvf2u2vumirgr5fkmvq.ipfs.dweb.link/', 'decimals': 0, 'isBooleanAmount': True, 'attributes': [{'name': 'token_id_offset', 'value': '1232907'}, {'name': 'series', 'value': 'GREEN'}]}"
                # )
                royalty = await Royalties.create(
                    id=id,
                    contract=contract,
                    token_id=token_id,
                    parts=[],
                    royalties_synced=False,
                    royalties_retries=0,
                    db_updated_at=datetime.now().strftime(date_pattern),
                )
                await process_royalties_for_token(ctx, royalty)

                # royalties
                saved = await Royalties.get_or_none(id=id)
                r0 = saved.parts

                self.assertEqual(1, len(r0))
                self.assertEqual("tz2DWt3yaJA9kuZRnV7cvTWsiXEabpwe6ASA", r0[0]['part_account'])
                self.assertEqual("1000", r0[0]['part_value'])

                # creator
                token = await Token.get_or_none(id=id)
                self.assertEqual('tz2RqGbjw67kHkFdCWkysjMkZVsNewg6pRhR', token.creator)

        async def test_royalties_kalamint_public(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1EpGgjQs73QfFJs9z7m1Mxm5MTnpC2tqse", "53057")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1gSCfWiPL8e6us331gtHCvJr9Cuf3jX8g6", r[0].part_account)
                self.assertEqual("1000", r[0].part_value)

        async def test_royalties_kalamint_private(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1RCzrLhBpdKXkyasKGpDTCcdbBTipUk77x", "5492")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1ZLRT3xiBgGRdNrTYXr8Stz4TppT3hukRi", r[0].part_account)
                self.assertEqual("700", r[0].part_value)

        async def test_royalties_fxhash_v1(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1KEa8z6vWXDJrVqtMrAeDVzsvxat3kHaCE", "522648")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1b8GULAVKS1oHpYLJbwuTKvUegXtRbxH82", r[0].part_account)
                self.assertEqual("1500", r[0].part_value)

        async def test_royalties_fxhash_v2(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1U6EHmNxJTkvaWJ4ThczG4FSDaHC21ssvi", "638313")
                self.assertEqual(2, len(r))
                self.assertEqual("tz1NpUTYsVB2Hdci6ycdWdTz66GvR5oLqQp8", r[0].part_account)
                self.assertEqual("550", r[0].part_value)
                self.assertEqual("tz1g1ZjehDWSJF9aGejq68rph4V24TTqCaRs", r[1].part_account)
                self.assertEqual("550", r[1].part_value)

        async def test_royalties_versum(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1LjmAdYQCLBjwv4S2oFkEzyHVkomAf5MrW", "19471")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1VNAyq17Xpz8QpbxMepbfdrcqNkomeKP35", r[0].part_account)
                self.assertEqual("2500", r[0].part_value)

        async def test_royalties_rarible(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT18pVpRXKPY2c4U2yFEGSH3ZnhB2kL8kwXS", "54686")
                self.assertEqual(1, len(r))
                self.assertEqual("tz2G4MMCYStTP9eUU35WQCqMSSJGtjJRZx9g", r[0].part_account)
                self.assertEqual("1000", r[0].part_value)

        async def test_royalties_objkt(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1EffErZNVCPXW2trCMD5gGkACdAbAzj4tT", "0")
                self.assertEqual(1, len(r))
                self.assertEqual("tz2L6ikhCEHz9rZnZWobd7jFSJ6KfkESSP88", r[0].part_account)
                self.assertEqual("1000", r[0].part_value)

        async def test_royalties_objkt_codecrafting(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1PNcZQkJXMQ2Mg92HG1kyrcu3auFX5pfd8", "897")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1SLgrDBpFWjGCnCwyNpCpQC1v8v2N8M2Ks", r[0].part_account)
                self.assertEqual("500", r[0].part_value)

        async def test_royalties_sweet_io(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1QkWhenHZGrRHjrpJMJKYtbJLLy1J6Zk5j", "149")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1e91CZhDWn5v4WAmYojVtKt7ECC5SNtf1c", r[0].part_account)
                self.assertEqual("1000", r[0].part_value)

        async def test_royalties_royalties_manager_with_token_id(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1N4Rrm6BU6229drs6scrH3vard1pPngMyA", "1")
                self.assertEqual(1, len(r))
                self.assertEqual("tz2L6ikhCEHz9rZnZWobd7jFSJ6KfkESSP88", r[0].part_account)
                self.assertEqual("1500", r[0].part_value)

        async def test_royalties_royalties_manager_without_token_id(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1LRLiZni9vRBUf78bzkKcAxTdchY1k5WjE", "1")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1bJhxQejTtMNLwxf4BcNpYrNmLRcFycShL", r[0].part_account)
                self.assertEqual("500", r[0].part_value)

        async def test_royalties_embedded_royalties(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1NVvPsNDChrLRH5K2cy6Sc9r1uuUwdiZQd", "8276")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1bj9NxKYups7WCFmytkYJTw6rxtizJR79K", r[0].part_account)
                self.assertEqual("700", r[0].part_value)

        async def test_royalties_bidou_8x8(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1MxDwChiDwd6WBVs24g1NjERUoK622ZEFp", "69")
                self.assertEqual(1, len(r))
                self.assertEqual("tz2QhmKtUWRyArfaqfBedvVdidgKpCcckMXV", r[0].part_account)
                self.assertEqual("1000", r[0].part_value)

        async def test_royalties_bidou_24x24(self) -> None:
            async with AsyncExitStack() as stack:
                dipdup = await create_test_dipdup(config, stack)
                ctx = dipdup._ctx
                r = await fetch_royalties(ctx, "KT1TR1ErEQPTdtaJ7hbvKTJSa1tsGnHGZTpf", "1853")
                self.assertEqual(1, len(r))
                self.assertEqual("tz1a9QWs5PdGwpaJ37PMqaYwzufbseDm1KWv", r[0].part_account)
                self.assertEqual("1500", r[0].part_value)
