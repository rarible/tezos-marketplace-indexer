CREATE TABLE IF NOT EXISTS public.ownership
(
    contract varchar(36)              not null,
    token_id text                     not null,
    owner    varchar(36)              not null,
    balance  numeric(176, 36)         not null,
    updated  timestamp with time zone not null,
    constraint ownership_id unique (contract, token_id, owner)
);

CREATE
    OR REPLACE FUNCTION update_ownership_balance()
    RETURNS TRIGGER
    LANGUAGE PLPGSQL
AS
$$
BEGIN

    -- debit
    if NEW.to_address notnull then
        insert into ownership (contract, token_id, owner, balance, updated)
        values (NEW.contract, NEW.token_id, NEW.to_address, NEW.amount, NEW.date)
        on conflict on constraint ownership_id do update set balance = ownership.balance + NEW.amount;
    end if;

    -- credit
    update ownership set balance = balance - NEW.amount, updated = NEW.date
    where contract = NEW.contract
      AND token_id = NEW.token_id
      AND owner = NEW.from_address;

    return NEW;
END
$$;

CREATE OR REPLACE TRIGGER on_insert
    AFTER INSERT
    ON "public"."token_transfer"
    FOR EACH ROW
EXECUTE FUNCTION update_ownership_balance();
