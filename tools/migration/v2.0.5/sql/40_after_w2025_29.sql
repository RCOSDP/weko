-- Model changes up to v2.0.5 that W2025-29.sql leaves out or applies
-- differently from the models. Idempotent.
BEGIN;

-- W2025-29.sql adds search_condition as VARCHAR(3); the model is String(20).
ALTER TABLE facet_search_setting ALTER COLUMN search_condition TYPE VARCHAR(20);

-- W2025-29.sql adds index.is_deleted as nullable; the model is NOT NULL.
UPDATE index SET is_deleted = false WHERE is_deleted IS NULL;
ALTER TABLE index ALTER COLUMN is_deleted SET NOT NULL;

-- rocrate_mapping is used by the item type admin and the records REST API,
-- but no script creates it (the AMS scripts only load data into it).
CREATE TABLE IF NOT EXISTS rocrate_mapping (
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    id SERIAL,
    item_type_id INTEGER NOT NULL,
    mapping JSONB,
    CONSTRAINT pk_rocrate_mapping PRIMARY KEY (id),
    CONSTRAINT uq_rocrate_mapping_item_type_id UNIQUE (item_type_id),
    CONSTRAINT fk_rocrate_mapping_item_type_id_item_type
        FOREIGN KEY (item_type_id) REFERENCES item_type (id)
);

-- W2025-29.sql creates extra_info as JSON NOT NULL DEFAULT '{}';
-- the model is a nullable JSONB.
ALTER TABLE file_onetime_download
    ALTER COLUMN extra_info DROP DEFAULT,
    ALTER COLUMN extra_info DROP NOT NULL,
    ALTER COLUMN extra_info TYPE JSONB USING extra_info::jsonb;

-- Indexes declared with index=True in weko-workspace.
CREATE INDEX IF NOT EXISTS ix_workspace_default_conditions_user_id
    ON workspace_default_conditions (user_id);
CREATE INDEX IF NOT EXISTS ix_workspace_status_management_user_id
    ON workspace_status_management (user_id);
CREATE INDEX IF NOT EXISTS ix_workspace_status_management_recid
    ON workspace_status_management (recid);

-- sitelicense_ip_address: the primary key became (organization_id,
-- organization_no). Databases created before 2021-12 already have it.
DO $$
DECLARE
    pk_name TEXT;
    pk_cols TEXT;
BEGIN
    SELECT c.conname, string_agg(a.attname, ',' ORDER BY a.attname)
      INTO pk_name, pk_cols
      FROM pg_constraint c
      JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
     WHERE c.conrelid = 'sitelicense_ip_address'::regclass AND c.contype = 'p'
     GROUP BY c.conname;
    IF pk_cols IS DISTINCT FROM 'organization_id,organization_no' THEN
        ALTER TABLE sitelicense_ip_address ALTER COLUMN organization_no SET NOT NULL;
        IF pk_name IS NOT NULL THEN
            EXECUTE format('ALTER TABLE sitelicense_ip_address DROP CONSTRAINT %I', pk_name);
        END IF;
        ALTER TABLE sitelicense_ip_address
            ADD CONSTRAINT pk_sitelicense_ip_address
            PRIMARY KEY (organization_id, organization_no);
        RAISE NOTICE 'sitelicense_ip_address: primary key changed from (%)', pk_cols;
    END IF;
END$$;

COMMIT;
