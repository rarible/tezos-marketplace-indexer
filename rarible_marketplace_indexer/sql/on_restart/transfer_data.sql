DO $$
    BEGIN
        BEGIN
            ALTER TABLE token_transfer ADD COLUMN tzkt_origination_id bigint;
        EXCEPTION
            WHEN duplicate_column THEN RAISE NOTICE 'column tzkt_origination_id already exists in token_transfer.';
        END;
    END;
$$
