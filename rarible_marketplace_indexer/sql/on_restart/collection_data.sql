create or replace view collection_with_meta as
select c.contract,
       c.owner,
       c.db_updated_at,
       dcm.metadata
from collection c
         left join dipdup_contract_metadata dcm on c.contract = dcm.contract;
