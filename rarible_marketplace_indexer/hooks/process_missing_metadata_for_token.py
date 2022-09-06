import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.models import Token, IndexEnum
from rarible_marketplace_indexer.utils.rarible_utils import process_metadata


async def process_missing_metadata_for_token(
        ctx: HookContext,
) -> None:
    logger = logging.getLogger("metadata_daemon")
    logger.info("starting metadata daemon")
    print("test")
    missing_meta_tokens: List[Token] = await Token.filter(
        metadata=None,
        metadata_retries__lt=5,
    ).limit(100)
    for token in missing_meta_tokens:
        token.metadata = await process_metadata(ctx, IndexEnum.NFT, f"{token.contract}:{token.token_id}")
        if token.metadata is None:
            token.metadata_retries = token.metadata_retries + 1
        await token.save()
        print(f"saved token {token.contract}:{token.token_id} with retries {token.metadata_retries}")
