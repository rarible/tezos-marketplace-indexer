import uuid

from rarible_marketplace_indexer.models import Ownership
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.ownership import RaribleApiOwnership, OwnershipBody


class RaribleApiOwnershipFactory:
    @staticmethod
    def build(ownership: Ownership, event_type: str) -> RaribleApiOwnership:
        random_id=uuid.uuid4()
        full_id = ownership.full_id()
        return RaribleApiOwnership(
            id=random_id,
            event_id=random_id,
            ownershipId=full_id,
            type=event_type,
            ownership=OwnershipBody(
                id=full_id,
                contract=ownership.contract,
                token_id=ownership.token_id,
                owner=ownership.owner,
                value=ownership.balance,
                date=ownership.updated
            )
        )
