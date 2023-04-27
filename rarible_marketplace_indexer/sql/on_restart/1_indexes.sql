-- drop index concurrently if exists token_transfer_contract_token_id;
-- create index concurrently if not exists token_transfer_hash ON token_transfer (hash);
create index concurrently if not exists token_transfer_contract_token_id_type ON token_transfer (contract, token_id, type); -- for royalty queries
-- create index concurrently if not exists royalties_retries_synced on royalties (royalties_synced, royalties_retries);
-- create index concurrently if not exists metadata_retries_synced on metadata_token (metadata_synced, metadata_retries);
--
create index concurrently if not exists marketplace_activity_operation_timestamp on marketplace_activity (operation_timestamp); -- remove later
create index concurrently if not exists marketplace_activity_type_operation_timestamp on marketplace_activity (type, operation_timestamp);
create index concurrently if not exists token_transfer_date on token_transfer (date);
create index concurrently if not exists marketplace_activity_request_by_item on marketplace_activity (make_contract, make_token_id);
create index concurrently if not exists marketplace_activity_request_by_item_graphql on marketplace_activity (make_token_id, make_contract, type);
create index concurrently if not exists idx_marketplace_order_by_maker on marketplace_order (maker, status);

create index concurrently if not exists ownership_owner on ownership (owner);

drop index concurrently if exists idx_marketplace_order_make_contract;
create index concurrently if not exists idx_marketplace_order_make_contract_graphql on marketplace_order (make_token_id, make_contract);
create index concurrently if not exists idx_marketplace_order_take_contract_graphql on marketplace_order (take_token_id, take_contract);

ALTER TABLE aggregator_event ADD COLUMN IF NOT EXISTS operation_timestamp timestamptz;
create index concurrently if not exists idx_aggregator_event_timestamp on aggregator_event (operation_timestamp);
create index concurrently if not exists idx_marketplace_activity_by_hash on marketplace_activity (operation_hash);
