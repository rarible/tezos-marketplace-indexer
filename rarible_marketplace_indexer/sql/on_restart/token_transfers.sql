create index concurrently if not exists token_transfer_hash ON token_transfer (hash);
drop index concurrently if exists token_transfer_contract_token_id;
create index concurrently if not exists token_transfer_contract_token_id_type ON token_transfer (contract, token_id, type); -- for royalty queries
