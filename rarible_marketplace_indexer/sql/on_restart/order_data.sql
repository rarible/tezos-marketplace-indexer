-- DO $$
--     BEGIN
--         BEGIN
--             ALTER TABLE marketplace_order ADD COLUMN is_bid boolean NOT NULL DEFAULT false;
--         EXCEPTION
--             WHEN duplicate_column THEN RAISE NOTICE 'column <column_name> already exists in <table_name>.';
--         END;
--     END;
-- $$

ALTER TABLE marketplace_order ADD COLUMN IF NOT EXISTS make_stock numeric(300,100);
