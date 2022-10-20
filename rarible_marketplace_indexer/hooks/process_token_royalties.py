import datetime
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
    fetch_start = datetime.datetime.now()
    royalties = await fetch_royalties(ctx, token_royalties.contract, token_royalties.token_id)
    fetch_end = datetime.datetime.now()
    log = ""
    if royalties is None:
        token_royalties.royalties_retries = token_royalties.royalties_retries + 1
        token_royalties.royalties_synced = False
        log = f"Royalties not found for {token_royalties.contract}:{token_royalties.token_id} (retries {token_royalties.royalties_retries})"

    else:
        try:
            token_royalties.parts = get_json_parts(royalties)
            token_royalties.royalties_synced = True
            token_royalties.royalties_retries = token_royalties.royalties_retries
            log = f"Successfully saved royalties for {token_royalties.contract}:{token_royalties.token_id} (retries {token_royalties.royalties_retries})"
            # token = await Token.get(id=Token.get_id(contract=token_royalties.contract,
            #                                         token_id=token_royalties.token_id))
            # token.creator = royalties[0].part_account
            # token_save_start = datetime.datetime.now()
            # await token.save()
            # token_save_end = datetime.datetime.now()
        except Exception as ex:
            log = f"Could not save royalties for {token_royalties.contract}:{token_royalties.token_id}: {ex}"
            token_royalties.royalties_retries = token_royalties.royalties_retries + 1
            token_royalties.royalties_synced = False
    royalties_save_start = datetime.datetime.now()
    await token_royalties.save()
    royalties_save_end = datetime.datetime.now()
    logger.info(log)

async def process_token_royalties(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").setLevel("INFO")
    logger.info("Running royalties job")

    done = False
    offset = 0
    ignore_list = ctx.config.custom.get("token_metadata_ignore_list") or []
    while not done:
        unsynced_royalties: List[Royalties] = await Royalties.filter(
            royalties_synced=False,
            royalties_retries__lt=5,
            contract__not_in=ignore_list
        ).limit(100).offset(offset).order_by("-db_updated_at")

        if len(unsynced_royalties) == 0:
            done = True
        for royalties in unsynced_royalties:
            pending_tasks.append(create_task(process_royalties_for_token(ctx, royalties)))
        offset += 100
    await gather(*pending_tasks)
    logger.info("Royalties job finished")
