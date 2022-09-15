import logging
from typing import cast

from dipdup.context import HandlerContext
from dipdup.models import Origination

from rarible_marketplace_indexer.types.tzprofile.storage import TzprofileStorage


async def on_tzprofile_factory_origination(
    ctx: HandlerContext,
    tzprofile_origination: Origination[TzprofileStorage],
) -> None:
    originated_contract = cast(str, tzprofile_origination.data.originated_contract_address)
    index_name = f"tzprofiles_{originated_contract}"
    try:
        await ctx.add_contract(
            name=originated_contract,
            address=originated_contract,
            typename="tzprofile",
        )
        await ctx.add_index(
            name=index_name,
            template="tzprofiles",
            values=dict(contract=originated_contract),
        )
    except Exception as ex:
        logging.getLogger("dipdup.tzprofile").info(f"Error while saving contract {originated_contract}: {ex}")
