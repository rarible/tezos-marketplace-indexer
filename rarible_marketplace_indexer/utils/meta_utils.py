import json
import logging

from rarible_marketplace_indexer.models import CollectionMetadata

logger = logging.getLogger("dipdup.meta_utils")


async def get_collection_meta(id):
    metadata = None
    meta = await CollectionMetadata.get_or_none(id=id)
    parser = 'json'
    if meta is not None:
        metadata = try_json(meta.metadata)
        if metadata is None:
            parser = 'single_quoted_json'
            metadata = try_single_quoted_json(meta.metadata)
        if metadata is None:
            parser = 'literal_eval'
            metadata = try_literal_eval(meta.metadata)
    if meta is not None and metadata is None:
        logger.warning(f"Metadata is empty for {id} failed on {parser}")
    return metadata


def try_json(val):
    try:
        return json.loads(val, strict=False)
    except Exception as err:
        logger.debug(f"Failed to parse json meta ({val}) {err=}, {type(err)=}")
        return None


def try_single_quoted_json(val):
    try:
        return json.loads(val.replace("'", '"'), strict=False)
    except Exception as err:
        logger.debug(f"Failed to parse single-quoted json meta ({val}) {err=}, {type(err)=}")
        return None


def try_literal_eval(val):
    try:
        return json.literal_eval(val)
    except Exception as err:
        logger.debug(f"Failed to literal eval meta ({val}) {err=}, {type(err)=}")
        return None
