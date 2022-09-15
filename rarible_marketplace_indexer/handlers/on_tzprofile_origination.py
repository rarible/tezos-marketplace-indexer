from dipdup.models import Origination
from dipdup.context import HandlerContext
from rarible_marketplace_indexer.models import TZProfile
from rarible_marketplace_indexer.types.tzprofile.storage import TzprofileStorage
from rarible_marketplace_indexer.utils.tzprofile_utils import resolve_profile


async def on_tzprofile_origination(
    ctx: HandlerContext,
    tzprofile_origination: Origination[TzprofileStorage],
) -> None:
    profile, created = await TZProfile.get_or_create(
        account=tzprofile_origination.storage.owner,
        defaults={
            "contract": tzprofile_origination.data.originated_contract_address,
            "valid_claims": [],
            "invalid_claims": [],
            "errored": False,
        },
    )
    if created:
        await resolve_profile(tzprofile_origination.storage.claims, profile)
        await profile.save()
