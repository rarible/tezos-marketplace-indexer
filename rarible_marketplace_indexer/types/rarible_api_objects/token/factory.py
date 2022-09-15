import uuid

from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import RaribleApiToken
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import TokenBody


class RaribleApiTokenFactory:
    @staticmethod
    def build_update(token: Token) -> RaribleApiToken:
        random_id = uuid.uuid4()
        full_id = token.full_id()
        return RaribleApiToken(
            id=random_id,
            event_id=random_id,
            item_id=full_id,
            type="UPDATE",
            item=TokenBody(
                id=full_id,
                contract=token.contract,
                token_id=token.token_id,
                creators=[],
                supply=token.supply,
                minted=token.minted,
                minted_at=token.minted_at,
                updated=token.updated,
                deleted=token.deleted,
            ),
        )

    @staticmethod
    def build_delete(token: Token) -> RaribleApiToken:
        random_id = uuid.uuid4()
        full_id = token.full_id()
        return RaribleApiToken(id=random_id, event_id=random_id, item_id=full_id, type="DELETE")
