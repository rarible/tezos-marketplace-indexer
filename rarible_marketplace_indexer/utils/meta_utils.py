import json
import logging

from rarible_marketplace_indexer.models import CollectionMetadata

logger = logging.getLogger("dipdup.meta_utils")


async def get_collection_meta(id):
    metadata = None
    try:
        meta = await CollectionMetadata.get_or_none(id=id)
        if meta is not None:
            metadata = json.loads(meta.metadata.replace("'", '"'), strict=False)
    except Exception as err:
        logger.error(f"Unexpected during getting name from meta ({id}) {err=}, {type(err)=}")
    return metadata
