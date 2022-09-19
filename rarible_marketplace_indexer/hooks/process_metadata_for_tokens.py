import logging
from typing import List

from dipdup.context import HookContext

from rarible_marketplace_indexer.metadata.metadata import process_metadata
from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.models import TokenMetadata


async def process_metadata_for_tokens(
    ctx: HookContext,
) -> None:
    logging.getLogger("dipdup.kafka").disabled = True
    logger = logging.getLogger("token_metadata")
    logger.info("Running token metadata job")
    missing_meta_tokens: List[Token] = await Token.filter(
        metadata_synced=False,
        metadata_retries__lt=5,
    ).limit(1000)
    for token in missing_meta_tokens:
        metadata = await process_metadata(ctx, IndexEnum.NFT, f"{token.contract}:{token.token_id}")
        if metadata is None:
            token.metadata_retries = token.metadata_retries + 1
            logger.warning(
                f"Metadata not found for {token.contract}:{token.token_id} (retries {token.metadata_retries})"
            )
        else:
            await TokenMetadata.update_or_create(
                id=TokenMetadata.get_id(token.contract, token.token_id),
                contract=token.contract,
                token_id=token.token_id,
                metadata=metadata,
            )
            token.metadata_synced = True
            logger.info(
                f"Successfully saved metadata for {token.contract}:{token.token_id} (retries {token.metadata_retries})"
            )
        await token.save()
    logger.info("Token metadata job finished")
