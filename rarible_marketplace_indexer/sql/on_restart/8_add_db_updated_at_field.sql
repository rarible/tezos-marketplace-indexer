-- DO $$
--     BEGIN
--         BEGIN
--             ALTER TABLE token_transfer ADD COLUMN db_updated_at timestamptz;
--         EXCEPTION
--             WHEN duplicate_column THEN RAISE NOTICE 'column db_updated_at already exists in token_transfer.';
--         END;
--     END;
-- $$;
-- create index concurrently if not exists token_transfer_db_updated_at on token_transfer (db_updated_at);
--
-- DO $$
--     BEGIN
--         BEGIN
--             ALTER TABLE marketplace_activity ADD COLUMN db_updated_at timestamptz;
--         EXCEPTION
--             WHEN duplicate_column THEN RAISE NOTICE 'column db_updated_at already exists in marketplace_activity.';
--         END;
--     END;
-- $$;
-- create index concurrently if not exists marketplace_activity_db_updated_at on marketplace_activity (db_updated_at);

update token_transfer set db_updated_at = null;
update marketplace_activity set db_updated_at = null;
