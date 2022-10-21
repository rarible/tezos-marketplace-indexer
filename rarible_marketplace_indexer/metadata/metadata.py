import json
import logging
from typing import Dict

import aiohttp
import requests
import warlock
from dipdup.context import DipDupContext

from rarible_marketplace_indexer.models import IndexEnum
from rarible_marketplace_indexer.utils.rarible_utils import get_bidou_data, get_string_id_big_map_key_hash, unpack_str, \
    get_token_id_big_map_key_hash
from rarible_marketplace_indexer.utils.rarible_utils import get_key_for_big_map

logger = logging.getLogger('metadata')
logger.setLevel("INFO")

collection_metadata_schema = {
    "$schema": "http://json-schema.org/draft-04/schema#",
    "$ref": "#/definitions/contractMetadataTzip16",
    "definitions": {
        "bignum": {"title": "Big number", "description": "Decimal representation of a big number", "type": "string"},
        "contractMetadataTzip16": {
            "title": "contractMetadataTzip16",
            "description": "Smart Contract Metadata Standard (TZIP-16).",
            "type": "object",
            "properties": {
                "name": {"description": "The identification of the contract.", "type": "string"},
                "description": {
                    "description": "Natural language description of the contract and/or its behavior.",
                    "type": "string",
                },
                "version": {"description": "The version of the contract code.", "type": "string"},
                "license": {
                    "description": "The software license of the contract.",
                    "type": "object",
                    "properties": {
                        "name": {
                            "description": "A mnemonic name for the license, see also the License-name case.",
                            "type": "string",
                        },
                        "details": {
                            "description": "Paragraphs of free text, with punctuation and proper language.",
                            "type": "string",
                        },
                    },
                    "required": ["name"],
                    "additionalProperties": False,
                },
                "authors": {
                    "description": "The list of authors of the contract.",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "homepage": {
                    "description": "A link for humans to follow for documentation, sources, issues, etc.",
                    "type": "string",
                },
                "source": {
                    "description": "Description of how the contract's Michelson was generated.",
                    "type": "object",
                    "properties": {
                        "tools": {
                            "title": "Contract Producing Tools",
                            "description": "List of tools/versions used in producing the Michelson.",
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "location": {
                            "title": "Source Location",
                            "description": "Location (URL) of the source code.",
                            "type": "string",
                        },
                    },
                    "additionalProperties": False,
                },
                "interfaces": {
                    "description": "The list of interfaces the contract claims to implement (e.g. TZIP-12).",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "errors": {
                    "description": "Error translators.",
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {
                                "title": "staticErrorTranslator",
                                "description": "A convertor between error codes and expanded messages.",
                                "type": "object",
                                "properties": {
                                    "error": {"$ref": "#/definitions/micheline.tzip-16.expression"},
                                    "expansion": {"$ref": "#/definitions/micheline.tzip-16.expression"},
                                    "languages": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["expansion", "error"],
                                "additionalProperties": False,
                            },
                            {
                                "title": "dynamicErrorTranslator",
                                "description": "An off-chain-view to call to convert error codes to expanded messages.",
                                "type": "object",
                                "properties": {
                                    "view": {"type": "string"},
                                    "languages": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["view"],
                                "additionalProperties": False,
                            },
                        ]
                    },
                },
                "views": {
                    "description": "The storage queries, a.k.a. off-chain views provided.",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {
                                "description": "Plain language documentation of the off-chain view; with punctuation.",
                                "type": "string",
                            },
                            "implementations": {
                                "description": "The list of available and equivalent implementations.",
                                "type": "array",
                                "items": {
                                    "oneOf": [
                                        {
                                            "title": "michelsonStorageView",
                                            "description": "An off-chain view using Michelson as a scripting "
                                                           "language to interpret the storage of a contract.",
                                            "type": "object",
                                            "properties": {
                                                "michelsonStorageView": {
                                                    "type": "object",
                                                    "properties": {
                                                        "parameter": {
                                                            "description": "The Michelson type of the potential "
                                                                           "external parameters required by the "
                                                                           "code of the view.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "returnType": {
                                                            "description": "The type of the result of the view, "
                                                                           "i.e. the value left on the stack by "
                                                                           "the code.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "code": {
                                                            "description": "The Michelson code expression implementing "
                                                                           "the view.",
                                                            "$ref": "#/definitions/micheline.tzip-16.expression",
                                                        },
                                                        "annotations": {
                                                            "description": "List of objects documenting the "
                                                                           "annotations used in the 3 above fields.",
                                                            "type": "array",
                                                            "items": {
                                                                "type": "object",
                                                                "properties": {
                                                                    "name": {"type": "string"},
                                                                    "description": {"type": "string"},
                                                                },
                                                                "required": ["description", "name"],
                                                                "additionalProperties": False,
                                                            },
                                                        },
                                                        "version": {
                                                            "description": "A string representing the version of "
                                                                           "Michelson that the view is meant to work "
                                                                           "with; versions here should be "
                                                                           "base58check-encoded protocol hashes.",
                                                            "type": "string",
                                                        },
                                                    },
                                                    "required": ["code", "returnType"],
                                                    "additionalProperties": False,
                                                }
                                            },
                                            "required": ["michelsonStorageView"],
                                            "additionalProperties": False,
                                        },
                                        {
                                            "title": "restApiQueryView",
                                            "description": "An off-chain view using a REST API described in a separate "
                                                           "OpenAPI specification. The following parameters form a "
                                                           "pointer to the localtion in the OpenAPI description.",
                                            "type": "object",
                                            "properties": {
                                                "restApiQuery": {
                                                    "type": "object",
                                                    "properties": {
                                                        "specificationUri": {
                                                            "description": "A URI pointing at the location of the "
                                                                           "OpenAPI specification.",
                                                            "type": "string",
                                                        },
                                                        "baseUri": {
                                                            "description": "The URI-prefix to use to query the API.",
                                                            "type": "string",
                                                        },
                                                        "path": {
                                                            "description": "The path component of the "
                                                                           "URI to look-up in "
                                                                           "the OpenAPI specification.",
                                                            "type": "string",
                                                        },
                                                        "method": {
                                                            "description": "The HTTP method to use.",
                                                            "type": "string",
                                                            "enum": ["GET", "POST", "PUT"],
                                                        },
                                                    },
                                                    "required": ["path", "specificationUri"],
                                                    "additionalProperties": False,
                                                }
                                            },
                                            "required": ["restApiQuery"],
                                            "additionalProperties": False,
                                        },
                                    ]
                                },
                            },
                            "pure": {"type": "boolean"},
                        },
                        "required": ["implementations", "name"],
                        "additionalProperties": False,
                    },
                },
            },
        },
        "micheline.tzip-16.expression": {
            "oneOf": [
                {
                    "title": "Int",
                    "type": "object",
                    "properties": {"int": {"$ref": "#/definitions/bignum"}},
                    "required": ["int"],
                    "additionalProperties": False,
                },
                {
                    "title": "String",
                    "type": "object",
                    "properties": {"string": {"$ref": "#/definitions/unistring"}},
                    "required": ["string"],
                    "additionalProperties": False,
                },
                {
                    "title": "Bytes",
                    "type": "object",
                    "properties": {"bytes": {"type": "string", "pattern": "^[a-zA-Z0-9]+$"}},
                    "required": ["bytes"],
                    "additionalProperties": False,
                },
                {"title": "Sequence", "type": "array", "items": {"$ref": "#/definitions/micheline.tzip-16.expression"}},
                {
                    "title": "Generic prim (any number of args with or without annot)",
                    "type": "object",
                    "properties": {
                        "prim": {"$ref": "#/definitions/unistring"},
                        "args": {"type": "array", "items": {"$ref": "#/definitions/micheline.tzip-16.expression"}},
                        "annots": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["prim"],
                    "additionalProperties": False,
                },
            ]
        },
        "unistring": {
            "title": "Universal string representation",
            "description": "Either a plain UTF8 string, or a sequence of bytes for strings "
                           "that contain invalid byte sequences.",
            "oneOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "properties": {
                        "invalid_utf8_string": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 255},
                        }
                    },
                    "required": ["invalid_utf8_string"],
                    "additionalProperties": False,
                },
            ],
        },
    },
}

token_metadata_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$ref": "#/definitions/asset",
    "title": "Rich Metadata",
    "definitions": {
        "asset": {
            "type": "object",
            "additionalProperties": True,
            "properties": {
                "description": {
                    "type": "string",
                    "description": "General notes, abstracts, or summaries about the contents of an asset.",
                },
                "minter": {
                    "type": "string",
                    "format": "tzaddress",
                    "description": "The tz address responsible for minting the asset.",
                },
                "creators": {
                    "type": "array",
                    "description": "The primary person, people, or organization(s) responsible for creating the "
                                   "intellectual content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "contributors": {
                    "type": "array",
                    "description": "The person, people, or organization(s) that have made substantial creative "
                                   "contributions to the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "publishers": {
                    "type": "array",
                    "description": "The person, people, or organization(s) primarily responsible for distributing "
                                   "or making the asset available to others in its present form.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "date": {
                    "type": "string",
                    "format": "date-time",
                    "description": "A date associated with the creation or availability of the asset.",
                },
                "blockLevel": {
                    "type": "integer",
                    "description": "Chain block level associated with the creation or availability of the asset.",
                },
                "type": {"type": "string", "description": "A broad definition of the type of content of the asset."},
                "tags": {
                    "type": "array",
                    "description": "A list of tags that describe the subject or content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "genres": {
                    "type": "array",
                    "description": "A list of genres that describe the subject or content of the asset.",
                    "uniqueItems": True,
                    "items": {"type": "string"},
                },
                "language": {
                    "type": "string",
                    "format": "https://tools.ietf.org/html/rfc1766",
                    "description": "The language of the intellectual content of the asset as defined in RFC 1776.",
                },
                "identifier": {
                    "type": "string",
                    "description": "A string or number used to uniquely identify the asset. "
                                   "Ex. URL, URN, UUID, ISBN, etc.",
                },
                "rights": {"type": "string", "description": "A statement about the asset rights."},
                "rightUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "Links to a statement of rights.",
                },
                "artifactUri": {"type": "string", "format": "uri-reference", "description": "A URI to the asset."},
                "displayUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to an image of the asset. Used for display purposes.",
                },
                "thumbnailUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to an image of the asset for wallets and client applications to "
                                   "have a scaled down image to present to end-users. "
                                   "Reccomened maximum size of 350x350px.",
                },
                "externalUri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI with additional information about the subject or content of the asset.",
                },
                "isTransferable": {
                    "type": "boolean",
                    "description": "All tokens will be transferable by default to allow end-users to send "
                                   "them to other end-users. However, this field exists to serve in special cases "
                                   "where owners will not be able to transfer the token.",
                },
                "isBooleanAmount": {
                    "type": "boolean",
                    "description": "Describes whether an account can have an amount of exactly 0 or 1. "
                                   "(The purpose of this field is for wallets to determine whether or not "
                                   "to display balance information and an amount field when transferring.)",
                },
                "shouldPreferSymbol": {
                    "type": "boolean",
                    "description": "Allows wallets to decide whether or not a symbol should be displayed "
                                   "in place of a name.",
                },
                "ttl": {
                    "type": "integer",
                    "description": "The maximum amount of time in seconds the asset metadata should be cached.",
                },
                "formats": {"type": "array", "items": {"$ref": "#/definitions/format"}},
                "attributes": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/attribute"},
                    "description": "Custom attributes about the subject or content of the asset.",
                },
                "assets": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/asset"},
                    "description": "Facilitates the description of collections and other types "
                                   "of resources that contain multiple assets.",
                },
            },
        },
        "format": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "uri": {
                    "type": "string",
                    "format": "uri-reference",
                    "description": "A URI to the asset represented in this format.",
                },
                "hash": {
                    "type": "string",
                    "description": "A checksum hash of the content of the asset in this format.",
                },
                "mimeType": {"type": "string", "description": "Media (MIME) type of the format."},
                "fileSize": {
                    "type": "integer",
                    "description": "Size in bytes of the content of the asset in this format.",
                },
                "fileName": {
                    "type": "string",
                    "description": "Filename for the asset in this format. For display purposes.",
                },
                "duration": {
                    "type": "string",
                    "format": "time",
                    "description": "Time duration of the content of the asset in this format.",
                },
                "dimensions": {
                    "$ref": "#/definitions/dimensions",
                    "description": "Dimensions of the content of the asset in this format.",
                },
                "dataRate": {
                    "$ref": "#/definitions/dataRate",
                    "description": "Data rate which the content of the asset in this format was captured at.",
                },
            },
        },
        "attribute": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "description": "Name of the attribute."},
                "value": {"type": "string", "description": "Value of the attribute."},
                "type": {"type": "string", "description": "Type of the value. To be used for display purposes."},
            },
            "required": ["name", "value"],
        },
        "dataRate": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"value": {"type": "integer"}, "unit": {"type": "string"}},
            "required": ["unit", "value"],
        },
        "dimensions": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"value": {"type": "string"}, "unit": {"type": "string"}},
            "required": ["unit", "value"],
        },
    },
}

CollectionMetadata = warlock.model_factory(collection_metadata_schema)
TokenMetadata = warlock.model_factory(token_metadata_schema)


def is_collection_metadata_valid(metadata):
    if metadata is None:
        return False
    try:
        CollectionMetadata(metadata)
        return True
    except Exception as error:
        logger.warning(f"Invalid metadata for collection {error}: {metadata}")
        return False


def is_token_metadata_valid(metadata):
    if metadata is None:
        return False
    try:
        TokenMetadata(metadata)
        return True
    except Exception as error:
        logger.warning(f"Invalid metadata for token {error}: {metadata}")
        return False


async def fetch_metadata(ctx: DipDupContext, metadata_url: str):
    if metadata_url is not None and metadata_url != b'':
        url = bytes.fromhex(metadata_url).decode("utf-8")
        if url.startswith("\x05\x01\x00\x00\x00"):
            url = unpack_str(bytes.fromhex(metadata_url))
        if url.startswith("http") or url.startswith("https"):
            response = requests.get(url)
            if response.ok:
                try:
                    return response.json()
                except requests.exceptions.JSONDecodeError:
                    logger.warning("Could not parse metadata, received invalid content")
                    return None
            else:
                logger.warning(f"Could not parse metadata: {response.status_code} {response.reason}")
                return None
        elif url.startswith("ipfs://ipfs/"):
            ipfs_hash = url.split("ipfs://ipfs/")[1]
            try:
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None
        elif url.startswith("ipfs://"):
            ipfs_hash = url.split("ipfs://")[1]
            try:
                if ipfs_hash == "undefined":
                    return None
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None
        elif url.startswith("ipfs:/"):
            ipfs_hash = url.split("ipfs:/")[1]
            try:
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None
        elif url.startswith("ifps://"):
            ipfs_hash = url.split("ifps://")[1]
            try:
                metadata = await ctx.get_ipfs_datasource("ipfs").get(ipfs_hash)
                return metadata
            except aiohttp.client_exceptions.ClientResponseError as error:
                logger.warning(f"Could not parse metadata: {error}")
                return None
        else:
            if url != "":
                try:
                    metadata = await ctx.get_ipfs_datasource("ipfs").get(url)
                    return metadata
                except aiohttp.client_exceptions.ClientResponseError as error:
                    logger.warning(f"Could not parse metadata: {error}")
                    return None


async def get_collection_metadata(ctx: DipDupContext, asset_id: str):
    try:
        contract_metadata = await ctx.get_metadata_datasource('metadata').get_contract_metadata(asset_id)
        if contract_metadata is None:
            metadata_url_raw = await get_key_for_big_map(ctx, asset_id, "metadata", get_string_id_big_map_key_hash(""))
            if metadata_url_raw is not None:
                metadata_url = metadata_url_raw.get("value")
                contract_metadata = await fetch_metadata(ctx, metadata_url)
            if contract_metadata is None:
                name_result = await get_key_for_big_map(ctx, asset_id, "metadata", get_string_id_big_map_key_hash(
                    "name"))
                if name_result is not None:
                    contract_metadata = {"name": bytes.fromhex(name_result.get("value")).decode("utf-8")}
            if contract_metadata is None:
                onchain_metadata_path = bytes.fromhex(metadata_url).decode("utf-8")
                splitted_onchain_metadata_path = onchain_metadata_path.split(":")
                if len(splitted_onchain_metadata_path) == 2:
                    onchain_metadata_key = splitted_onchain_metadata_path[1]
                    onchain_metadata_result = await get_key_for_big_map(ctx, asset_id, "metadata",
                                                                        get_string_id_big_map_key_hash(onchain_metadata_key))
                    onchain_metadata_raw = onchain_metadata_result.get("value")
                    if onchain_metadata_raw is not None:
                        contract_metadata = json.loads(bytes.fromhex(onchain_metadata_raw).decode("utf-8"))
        return contract_metadata
    except Exception as ex:
        logging.getLogger('collection_metadata').warning(f"Could not fetch metadata for collection {asset_id}: {ex}")
        return None
    # if is_collection_metadata_valid(contract_metadata):
    #     return contract_metadata
    # else:
    #     return None


async def get_token_metadata(ctx: DipDupContext, asset_id: str):
    try:
        known_addresses: Dict[str, str] = ctx.config.custom.get("royalties")
        parsed_id = asset_id.split(":")
        if len(parsed_id) != 2:
            raise Exception(f"Invalid Token ID: {asset_id}")
        contract = parsed_id[0]
        token_id = parsed_id[1]
        if contract in [known_addresses.get("bidou_8x8"), known_addresses.get("bidou_24x24"), known_addresses.get(
                "bidou_24x24_color")]:
            bidou_metadata = await get_bidou_data(ctx, contract, token_id)
            creater = bidou_metadata.get("creater")
            creator = bidou_metadata.get("creator")
            creater_name = bidou_metadata.get("creater_name")
            creator_name = bidou_metadata.get("creator_name")
            account = creater if creater is not None else creator
            name = creater_name if creater_name is not None else creator_name
            token_metadata = {
                "name": bidou_metadata.get("token_name"),
                "description": bidou_metadata.get("token_description"),
                "content": [
                    {"uri": "", "mimeType": "image/jpeg", "representation": "PREVIEW"},
                    {"uri": "", "mimeType": "image/jpeg", "representation": "ORIGINAL"},
                ],
                "attributes": [{"creator": account}, {"creator_name": name}],
            }
        else:
            token_metadata = await ctx.get_metadata_datasource('metadata').get_token_metadata(contract, int(token_id))
            if token_metadata is None:
                logging.getLogger('token_metadata').warning(f"Could not fetch metadata for token from dipdup{asset_id}")

                metadata_url_response = await get_key_for_big_map(ctx, contract, "token_metadata",
                                                                  get_token_id_big_map_key_hash(token_id))
                if metadata_url_response is not None:
                    metadata_raw = metadata_url_response.get("value")
                    token_info = metadata_raw.get("token_info")
                    metadata_url = token_info.get("")
                    if metadata_url is None and token_info is not None:
                        token_metadata = token_info
                    else:
                        if metadata_url is not None:
                            if metadata_url != "":
                                logging.getLogger('token_metadata').info(
                                    f"Fetching from ipfs metadata for {asset_id}")
                                token_metadata = await fetch_metadata(ctx, metadata_url)
        return token_metadata
    # if is_token_metadata_valid(token_metadata):
    #     return token_metadata
    # else:
    #     return None
    except Exception as ex:
        logging.getLogger('token_metadata').warning(f"Could not fetch metadata for token {asset_id}: {ex}")
        return None


async def process_metadata(ctx: DipDupContext, asset_type: str, asset_id: str):
    try:
        if asset_type is IndexEnum.COLLECTION:
            metadata = await get_collection_metadata(ctx, asset_id)
            return metadata
        elif asset_type is IndexEnum.NFT:
            metadata = await get_token_metadata(ctx, asset_id)
            return metadata
    except Exception as ex:
        logging.getLogger("metadata").warning(f"Couldn't process metadata for asset {asset_id}: {ex}")
        return None
