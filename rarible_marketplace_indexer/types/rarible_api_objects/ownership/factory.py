import uuid

from rarible_marketplace_indexer.models import Ownership
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.ownership import OwnershipBody
from rarible_marketplace_indexer.types.rarible_api_objects.ownership.ownership import RaribleApiOwnership


class RaribleApiOwnershipFactory:
    @staticmethod
    def build_update(ownership: Ownership) -> RaribleApiOwnership:
        random_id = uuid.uuid4()
        full_id = ownership.full_id()
        return RaribleApiOwnership(
            id=random_id,
            event_id=random_id,
            ownership_id=full_id,
            type="UPDATE",
            ownership=OwnershipBody(
                id=full_id,
                contract=ownership.contract,
                token_id=ownership.token_id,
                owner=ownership.owner,
                value=ownership.balance,
                date=ownership.updated,
            ),
        )

    @staticmethod
    def build_delete(ownership: Ownership) -> RaribleApiOwnership:
        random_id = uuid.uuid4()
        full_id = ownership.full_id()
        return RaribleApiOwnership(id=random_id, event_id=random_id, ownership_id=full_id, type="DELETE")
