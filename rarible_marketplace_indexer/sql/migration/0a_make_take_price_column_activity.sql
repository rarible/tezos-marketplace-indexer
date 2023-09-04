ALTER TABLE marketplace_activity
ADD COLUMN IF NOT EXISTS make_price numeric(300,100),
ADD COLUMN IF NOT EXISTS take_price numeric(300,100);