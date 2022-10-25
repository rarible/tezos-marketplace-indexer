DROP VIEW IF EXISTS token_by_owner;
DROP VIEW IF EXISTS token_with_meta;

ALTER TABLE marketplace_activity
ALTER COLUMN take_token_id SET DATA TYPE varchar(256);

ALTER TABLE marketplace_activity
ALTER COLUMN make_token_id SET DATA TYPE varchar(256);

ALTER TABLE marketplace_order
ALTER COLUMN take_token_id SET DATA TYPE varchar(256);

ALTER TABLE marketplace_order
ALTER COLUMN make_token_id SET DATA TYPE varchar(256);

ALTER TABLE metadata_token
ALTER COLUMN token_id SET DATA TYPE varchar(256);

ALTER TABLE ownership
ALTER COLUMN token_id SET DATA TYPE varchar(256);

ALTER TABLE royalties
ALTER COLUMN token_id SET DATA TYPE varchar(256);

ALTER TABLE token
ALTER COLUMN token_id SET DATA TYPE varchar(256);

ALTER TABLE token_transfer
ALTER COLUMN token_id SET DATA TYPE varchar(256);