-- drop index concurrently if exists token_transfer_contract_token_id;
-- create index concurrently if not exists token_transfer_hash ON token_transfer (hash);
create index concurrently if not exists token_transfer_contract_token_id_type ON token_transfer (contract, token_id, type); -- for royalty queries
-- create index concurrently if not exists royalties_retries_synced on royalties (royalties_synced, royalties_retries);
-- create index concurrently if not exists metadata_retries_synced on metadata_token (metadata_synced, metadata_retries);
--
create index concurrently if not exists marketplace_activity_operation_timestamp on marketplace_activity (operation_timestamp);
create index concurrently if not exists token_transfer_date on token_transfer (date);
