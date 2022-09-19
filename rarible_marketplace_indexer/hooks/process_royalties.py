import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Royalties
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.royalties.royalties import fetch_royalties
from rarible_marketplace_indexer.utils.rarible_utils import get_json_parts


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
        royalties = await fetch_royalties(ctx, token.contract, token.token_id)
        if royalties is None:
            token.royalties_retries = token.royalties_retries + 1
            logger.warning(
                f"Royalties not found for {token.contract}:{token.token_id} (retries {token.royalties_retries})"
            )
        else:
            await Royalties.update_or_create(
                id=Royalties.get_id(token.contract, token.id),
                contract=token.contract,
                token_id=token.token_id,
                parts=get_json_parts(royalties),
            )
            token.royalties_synced = True
            token.creator = royalties[0].part_account
            logger.info(
                f"Successfully saved royalties for {token.contract}:{token.token_id} (retries {token.metadata_retries})"
            )
        await token.save()
    logger.info("Royalties job finished")
