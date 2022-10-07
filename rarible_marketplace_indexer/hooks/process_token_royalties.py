import logging
from asyncio import create_task
from asyncio import gather
from collections import deque
from typing import Deque
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Royalties, Token
from rarible_marketplace_indexer.royalties.royalties import fetch_royalties
from rarible_marketplace_indexer.utils.rarible_utils import get_json_parts

pending_tasks = deque()
royalties_to_update: Deque[Royalties] = deque()
logger = logging.getLogger("token_royalties")
logger.setLevel("INFO")


async def process_royalties_for_token(ctx: HookContext, token_royalties: Royalties):
    royalties = await fetch_royalties(ctx, token_royalties.contract, token_royalties.token_id)
    if royalties is None:
        token_royalties.royalties_retries = token_royalties.royalties_retries + 1
        token_royalties.royalties_synced = False
        logger.warning(
            f"Royalties not found for {token_royalties.contract}:{token_royalties.token_id} "
            f"(retries {token_royalties.royalties_retries})"
        )
    else:
        try:
            token_royalties.parts = get_json_parts(royalties)
            token_royalties.royalties_synced = True
            token_royalties.royalties_retries = token_royalties.royalties_retries
            logger.info(
                f"Successfully saved royalties for {token_royalties.contract}:{token_royalties.token_id} "
                f"(retries {token_royalties.royalties_retries})"
            )
            token = await Token.get(id=Token.get_id(contract=token_royalties.contract,
                                                   token_id=token_royalties.token_id))
            token.creator = royalties[0].part_account
            await token.save()
        except Exception as ex:
            logger.warning(f"Could not save royalties for {token_royalties.contract}:{token_royalties.token_id}: {ex}")
            token_royalties.royalties_retries = token_royalties.royalties_retries + 1
            token_royalties.royalties_synced = False
    await token_royalties.save()


async def process_token_royalties(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").setLevel("INFO")
    logger.info("Running royalties job")
    unsynced_royalties: List[Royalties] = await Royalties.filter(
        royalties_synced=False,
        royalties_retries__lt=5,
    ).limit(100)
    if len(unsynced_royalties) > 0:
        for royalties in unsynced_royalties:
            pending_tasks.append(create_task(process_royalties_for_token(ctx, royalties)))
        await gather(*pending_tasks)
    logger.info("Royalties job finished")
