import uuid

from rarible_marketplace_indexer.models import Token
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import RaribleApiToken
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import RaribleItemMeta
from rarible_marketplace_indexer.types.rarible_api_objects.token.token import TokenBody
from rarible_marketplace_indexer.types.rarible_exchange.parameter.sell import Part


class RaribleApiTokenFactory:
    @staticmethod
    def build_update(token: Token) -> RaribleApiToken:
        random_id = uuid.uuid4()
        full_id = token.full_id()
        creators = []
        if token.creator is not None:
            creators.append(Part(part_account=token.creator, part_value=10000))
        return RaribleApiToken(
            id=random_id,
            event_id=random_id,
            item_id=full_id,
            type="UPDATE",
            item=TokenBody(
                id=full_id,
                contract=token.contract,
                token_id=token.token_id,
                creators=creators,
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

    @staticmethod
    def build_meta_update(token: Token) -> RaribleItemMeta:
        random_id = uuid.uuid4()
        full_id = token.full_id()
        return RaribleItemMeta(id=random_id, item_id=full_id, type='UPDATE')
