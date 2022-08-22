
ALTER TABLE public.ownership DROP CONSTRAINT IF EXISTS ownership_id;
ALTER TABLE public.ownership ADD CONSTRAINT ownership_id UNIQUE (contract, token_id, owner);

CREATE
    OR REPLACE FUNCTION update_ownership_balance()
    RETURNS TRIGGER
    LANGUAGE PLPGSQL
AS
$$
BEGIN

    -- mint
    if NEW.from_address isnull then
        insert into token (id, contract, token_id, minted_at, minted, supply, deleted, updated)
        values (NEW.tzkt_token_id, NEW.contract, NEW.token_id, NEW.date, NEW.amount, NEW.amount, false, NEW.date)
        on conflict on constraint token_pkey do update set minted = token.minted + NEW.amount, supply = token.supply + NEW.amount, updated = NEW.date;
    end if;

    -- burn
    if NEW.to_address isnull then
        update token set supply = token.supply - NEW.amount, updated = NEW.date
        where contract = NEW.contract and token_id = NEW.token_id;

        update token set deleted = true
        where contract = NEW.contract and token_id = NEW.token_id and token.supply = 0;
    end if;

    -- debit
    if NEW.to_address notnull then
        insert into ownership (contract, token_id, owner, balance, updated)
        values (NEW.contract, NEW.token_id, NEW.to_address, NEW.amount, NEW.date)
        on conflict on constraint ownership_id do update set balance = ownership.balance + NEW.amount, updated = NEW.date;
    end if;

    -- credit
    if NEW.from_address notnull then
        update ownership set balance = balance - NEW.amount, updated = NEW.date
        where contract = NEW.contract
          and token_id = NEW.token_id
          and owner = NEW.from_address
          and (balance - NEW.amount) > 0;

        -- clear
        delete
        from ownership
        where contract = NEW.contract
          and token_id = NEW.token_id
          and owner = NEW.from_address
          and (balance - NEW.amount) = 0;
    end if;

    return NEW;
END
$$;

CREATE OR REPLACE TRIGGER on_insert
    AFTER INSERT
    ON "public"."token_transfer"
    FOR EACH ROW
    WHEN ( NEW.amount > 0 )
EXECUTE FUNCTION update_ownership_balance();
