create or replace view token_with_meta as
select t.id,
       t.minted,
       t.minted_at,
       t.supply,
       t.token_id,
       t.updated,
       t.contract,
       t.creator,
       t.deleted,
       t.tzkt_id,
       tm.metadata
from token t
         left join metadata_token tm on t.id = tm.id;

create or replace view token_by_owner as
select t.*, o.owner from ownership o
    join token t on o.contract = t.contract and o.token_id = t.token_id
    order by t.updated desc, t.id desc;
