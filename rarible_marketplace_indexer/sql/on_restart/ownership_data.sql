-- CREATE TABLE IF NOT EXISTS public.ownership
-- (
--     id       serial                   not null,
--     contract varchar(36)              not null,
--     token_id text                     not null,
--     owner    varchar(36)              not null,
--     balance  numeric(176, 36)         not null,
--     updated  timestamp with time zone not null,
--     constraint ownership_id unique (contract, token_id, owner)
-- );
ALTER TABLE public.ownership DROP CONSTRAINT IF EXISTS ownership_id;
ALTER TABLE public.ownership ADD CONSTRAINT ownership_id UNIQUE (contract, token_id, owner);

CREATE
    OR REPLACE FUNCTION update_ownership_balance()
    RETURNS TRIGGER
    LANGUAGE PLPGSQL
AS
$$
BEGIN

    -- debit
    if NEW.to_address notnull and NEW.amount > 0 then
        insert into ownership (contract, token_id, owner, balance, updated)
        values (NEW.contract, NEW.token_id, NEW.to_address, NEW.amount, NEW.date)
        on conflict on constraint ownership_id do update set balance = ownership.balance + NEW.amount;
    end if;

    -- credit
    update ownership
    set balance = balance - NEW.amount,
        updated = NEW.date
    where contract = NEW.contract
      and token_id = NEW.token_id
      and owner = NEW.from_address
      and NEW.amount > 0
      and (balance - NEW.amount) > 0;

    -- clear
    delete
    from ownership
    where contract = NEW.contract
      and token_id = NEW.token_id
      and owner = NEW.from_address
      and (balance - NEW.amount) <= 0;

    return NEW;
END
$$;

CREATE OR REPLACE TRIGGER on_insert
    AFTER INSERT
    ON "public"."token_transfer"
    FOR EACH ROW
EXECUTE FUNCTION update_ownership_balance();
