-- delete from token_transfer where length(token_id) > 256;
-- delete from token where length(token_id) > 256;
-- delete from ownership where length(token_id) > 256;
-- delete from royalties where length(token_id) > 256;
-- delete from metadata_token where length(token_id) > 256;
-- delete from marketplace_order where length(make_token_id) > 256;
-- delete from marketplace_order where length(take_token_id) > 256;
-- delete from marketplace_activity where length(make_token_id) > 256;
-- delete from marketplace_activity where length(take_token_id) > 256;
--
--
drop index if exists idx_marketplace_activity_by_hash;
drop index if exists idx_metadata_co_metadat_721bd1;
drop index if exists idx_metadata_to_metadat_caffa0;
drop index if exists metadata_retries_synced;
drop index if exists token_transfer_date;
drop index if exists idx_aggregator__tracker_66ec96;
drop index if exists idx_aggregator__level_96452e;