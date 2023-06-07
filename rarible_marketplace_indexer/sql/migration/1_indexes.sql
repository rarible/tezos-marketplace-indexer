-- drop index concurrently if exists token_transfer_contract_token_id;
-- create index concurrently if not exists token_transfer_hash ON token_transfer (hash);
create index if not exists token_transfer_contract_token_id_type ON token_transfer (contract, token_id, type); -- for royalty queries
-- create index concurrently if not exists royalties_retries_synced on royalties (royalties_synced, royalties_retries);

create index if not exists metadata_retries_synced on metadata_token (metadata_synced, metadata_retries);
--
create index if not exists marketplace_activity_operation_timestamp on marketplace_activity (operation_timestamp); -- remove later
create index if not exists marketplace_activity_type_operation_timestamp on marketplace_activity (type, operation_timestamp);
create index if not exists token_transfer_date on token_transfer (date);
create index if not exists marketplace_activity_request_by_item on marketplace_activity (make_contract, make_token_id);
create index if not exists marketplace_activity_request_by_item_graphql on marketplace_activity (make_token_id, make_contract, type);
create index if not exists idx_marketplace_order_by_maker on marketplace_order (maker, status);

drop index if exists marketplace_activity_db_updated_at;
create index if not exists marketplace_activity_db_updated_at_id on marketplace_activity (db_updated_at, id);

drop index if exists token_transfer_db_updated_at;
create index if not exists token_transfer_db_updated_at_id on token_transfer (db_updated_at, id);

create index if not exists ownership_owner on ownership (owner);

drop index if exists idx_marketplace_order_make_contract;
create index if not exists idx_marketplace_order_make_contract_graphql on marketplace_order (make_token_id, make_contract);
create index if not exists idx_marketplace_order_take_contract_graphql on marketplace_order (take_token_id, take_contract);

create index if not exists idx_marketplace_order_platform on marketplace_order (platform, id);
drop index if exists idx_marketplace_platfor_66298d;

drop index if exists idx_marketplace_network_f26818;
drop index if exists idx_marketplace_interna_7a63f1;

ALTER TABLE aggregator_event ADD COLUMN IF NOT EXISTS operation_timestamp timestamptz;
create index if not exists idx_aggregator_event_timestamp on aggregator_event (operation_timestamp);
create index if not exists idx_marketplace_activity_by_hash on marketplace_activity (operation_hash);

create index if not exists idx_marketplace_order_ended_at_active ON marketplace_order (end_at) where status = 'ACTIVE';
