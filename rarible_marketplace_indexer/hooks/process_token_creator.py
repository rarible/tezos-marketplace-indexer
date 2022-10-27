import logging
from asyncio import create_task
from asyncio import gather
from collections import deque
from typing import Deque
from typing import List

from dipdup.context import HookContext
from rarible_marketplace_indexer.models import Royalties, Token, TokenTransfer, ActivityTypeEnum

pending_tasks = deque()
royalties_to_update: Deque[Royalties] = deque()
logger = logging.getLogger("token_creator")
logger.setLevel("INFO")


async def process_creator_for_token(ctx: HookContext, token: Token):
    royalties = await Royalties.get(id=token.id)
    log = ""
    if royalties is not None and len(royalties.parts) > 0:
        mint: TokenTransfer = await TokenTransfer.get(contract=token.contract, token_id=token.token_id, type=ActivityTypeEnum.TOKEN_MINT)
        if mint is not None:
            token.creator = mint.to_address
            await token.save()
            log = f"Creator not found for {token.contract}:{token.token_id}, using first owner"
        else:
            log = f"Creator not found for {token.contract}:{token.token_id}"
    else:
        try:
            token.creator = royalties.parts[0].get('part_account')
            await token.save()
            log = f"Successfully saved creator for {token.contract}:{token.token_id}"
        except Exception as ex:
            log = f"Could not save creator for {token.contract}:{token.token_id}: {ex}"
    logger.info(log)

async def process_token_creator(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logging.getLogger('apscheduler.scheduler').disabled = True
    logging.getLogger('dipdup.http').disabled = True
    logger.info("Running creator job")

    done = False
    offset = 0
    while not done:
        unsynced_creators: List[Token] = await Token.filter(
            creator=None,
        ).limit(100).offset(offset)

        if len(unsynced_creators) == 0:
            done = True
        for royalties in unsynced_creators:
            pending_tasks.append(create_task(process_creator_for_token(ctx, royalties)))
        offset += 100
    await gather(*pending_tasks)
    logger.info("Creator job finished")
