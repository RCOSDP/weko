CREATE TABLE public.item_billing (
    created     timestamp   NOT NULL,
    updated     timestamp   NOT NULL,
    item_id     int4        NOT NULL,
    role_id     int4        NOT NULL,
    include_tax bool        DEFAULT false,
    price       int4        DEFAULT NULL,
    CONSTRAINT pk_item_billing PRIMARY KEY (item_id, role_id)
);
ALTER TABLE public.item_billing ADD CONSTRAINT fk_item_billing_role_id_accounts_role FOREIGN KEY (role_id) REFERENCES accounts_role(id) ON DELETE CASCADE;
