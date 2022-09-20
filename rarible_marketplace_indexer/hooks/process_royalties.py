import logging
from asyncio import create_task, gather
from collections import deque
from typing import List, Deque

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Royalties
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.royalties.royalties import fetch_royalties


pending_tasks = deque()
tokens_to_update: Deque[Token] = deque()
royalties_to_update: Deque[Royalties] = deque()


async def process_token_royalties(ctx, token):
    logger = logging.getLogger("royalties")
    royalties = await fetch_royalties(ctx, token.contract, token.token_id)
    if royalties is None:
        token.royalties_retries = token.royalties_retries + 1
        token.royalties_synced = False
        logger.warning(
            f"Royalties not found for {token.contract}:{token.token_id} (retries {token.royalties_retries})"
        )
    else:
        try:
            token_royalties = await Royalties.get_or_none(
                id=token.id,
            )
            token_royalties.parts = royalties
            token.royalties_synced = True
            token.royalties_retries = token.royalties_retries
            royalties_to_update.append(token_royalties)
            logger.info(
                f"Successfully saved royalties for {token.contract}:{token.token_id} (retries {token.royalties_retries})"
            )
        except Exception as ex:
            logger.warning(f"Could not save royalties for {token.contract}:{token.token_id}: {ex}")
            token.royalties_retries = token.royalties_retries + 1
            token.royalties_synced = False
    tokens_to_update.append(token)


async def process_royalties(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("royalties")
    logger.setLevel("INFO")
    logger.info("Running royalties job")
    missing_royalties_tokens: List[Token] = await Token.filter(
        royalties_synced=False,
        royalties_retries__lt=5,
    ).limit(1000)
    for token in missing_royalties_tokens:
        pending_tasks.append(create_task(process_token_royalties(ctx, token)))
    await gather(*pending_tasks)
    await Token.bulk_update(tokens_to_update, fields=["royalties_synced", "royalties_retries"])
    await Royalties.bulk_update(royalties_to_update, fields=["parts"])
    logger.info("Royalties job finished")
