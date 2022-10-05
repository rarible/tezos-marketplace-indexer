create or replace view token_with_meta as
select t.id,
       t.minted,
       t.minted_at,
       t.supply,
       t.token_id,
       t.updated,
       t.contract,
       t.deleted,
       t.tzkt_id,
       tm.metadata
from token t
         left join metadata_token tm on t.id = tm.id;
create index concurrently if not exists token_transfer_hash ON dipdup.public.token_transfer (hash);
