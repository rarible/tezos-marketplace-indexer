create index concurrently if not exists token_transfer_hash ON token_transfer (hash);
create index concurrently if not exists token_transfer_contract_token_id ON token_transfer (contract, token_id); -- for queries by items
