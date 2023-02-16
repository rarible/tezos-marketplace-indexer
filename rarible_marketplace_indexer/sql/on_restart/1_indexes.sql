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
create index concurrently if not exists ownership_owner on ownership (owner);
create index concurrently if not exists idx_marketplace_order_make_contract on marketplace_order (make_contract, make_token_id);
