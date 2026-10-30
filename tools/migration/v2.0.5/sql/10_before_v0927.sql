-- Schema changes made between v0.9.20 and v1.0.8 that W2025-29.sql assumes
-- are already applied. These are idempotent rewrites of
--   postgresql/ddl/pr873.sql, pr1025.sql, pr1274.sql, fix_issue_37699.sql,
--   61660.sql and the authors conversion in postgresql/update/2023_Q4.sql.
-- The original files cannot be rerun (no IF NOT EXISTS), and pr1274.sql and
-- 2023_Q4.sql add the same column.
BEGIN;

-- pr1025.sql / 61660.sql
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_endpoint_url VARCHAR(128);
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_send_file_directly BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS readonly_access_key VARCHAR(128);
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS readonly_secret_key VARCHAR(128);

-- pr1025.sql: activity counter. Activity ids are numbered by the UTC date
-- (weko_workflow/api.py), so the first row uses the UTC date as well.
CREATE TABLE IF NOT EXISTS workflow_activity_count (
    status VARCHAR(1) NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    date DATE NOT NULL,
    activity_count INTEGER NOT NULL,
    CONSTRAINT pk_workflow_activity_count PRIMARY KEY (date)
);
INSERT INTO workflow_activity_count (status, created, updated, date, activity_count)
VALUES ('N', now(), now(), (now() AT TIME ZONE 'UTC')::date,
        (SELECT count(*) FROM workflow_activity
          WHERE created >= (now() AT TIME ZONE 'UTC')::date))
ON CONFLICT (date) DO NOTHING;

-- pr1025.sql: weko_admin/admin.py fails without this row.
INSERT INTO admin_settings (id, name, settings)
VALUES ((SELECT COALESCE(MAX(id), 0) + 1 FROM admin_settings),
        'elastic_reindex_settings', '{"has_errored": false}')
ON CONFLICT (name) DO NOTHING;
SELECT setval('admin_settings_id_seq', (SELECT MAX(id) FROM admin_settings));

-- pr1274.sql / 2023_Q4.sql
ALTER TABLE mail_config ADD COLUMN IF NOT EXISTS mail_local_hostname VARCHAR(255) DEFAULT '';

-- fix_issue_37699.sql / 2023_Q4.sql
ALTER TABLE shibboleth_user ALTER COLUMN shib_eppn TYPE VARCHAR(2310);

-- pr873.sql. 'Editbox' and 'Range' in the original are not values the
-- v2.0.5 admin screen offers, so existing rows get 'SelectBox' and a
-- display order that follows the id.
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS is_open BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS ui_type VARCHAR(20) NOT NULL DEFAULT 'SelectBox';
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS display_number INTEGER;
UPDATE facet_search_setting f SET display_number = o.n
  FROM (SELECT id, row_number() OVER (ORDER BY id) AS n FROM facet_search_setting) o
 WHERE f.id = o.id AND f.display_number IS NULL;

-- 2023_Q4.sql: authors.json held a JSON string instead of an object.
UPDATE authors SET json = (json #>> '{}')::jsonb WHERE jsonb_typeof(json) = 'string';

COMMIT;
