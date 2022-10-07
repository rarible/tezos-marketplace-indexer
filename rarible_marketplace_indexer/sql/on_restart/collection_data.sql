create or replace view collection_with_meta as
select c.id,
       c.owner,
       c.db_updated_at,
       cm.metadata
from collection c
         left join metadata_collection cm on c.id = cm.id;