import logging
import os
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Token, IndexEnum
from rarible_marketplace_indexer.utils.rarible_utils import process_metadata


async def process_missing_metadata_for_token(
        ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("token_metadata")
    logger.info("Starting token metadata job")
    missing_meta_tokens: List[Token] = await Token.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(1000)
    for token in missing_meta_tokens:
        metadata = await process_metadata(ctx, IndexEnum.NFT, f"{token.contract}:{token.token_id}")
        if metadata is None:
            token.metadata_retries = token.metadata_retries + 1
            logger.warning(f"Metadata not found for {token.contract}:{token.token_id} (retries {token.metadata_retries})")
        else:
            await ctx.update_token_metadata(os.getenv('NETWORK'), token.contract, token.token_id, metadata)
            token.metadata_synced = True
            logger.info(f"Successfully saved metadata for {token.contract}:{token.token_id} (retries {token.metadata_retries})")
        await token.save()
