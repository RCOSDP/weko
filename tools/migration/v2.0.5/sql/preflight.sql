-- Read-only checks run against the database before the upgrade.
-- Every query only reads; the output is kept in the log directory and
-- compared with verify.sql after the upgrade.
\pset footer off
\echo '== item types used by the default mappings (30001/30002 are created from 15/16 by fix_itemtype_issue_45614)'
SELECT id, name_id, harvesting_type, is_deleted FROM item_type WHERE id IN (15, 16, 30001, 30002) ORDER BY id;

\echo '== item_type_property count (update_v0927 runs only when > 53)'
SELECT count(*) AS item_type_property FROM item_type_property;

\echo '== records whose owner is not numeric (W2025-29.sql casts owner to numeric and fails on these)'
SELECT count(*) AS non_numeric_owner
  FROM records_metadata
 WHERE json ? 'owner' AND NOT (json->>'owner' ~ '^[0-9]+$');

\echo '== primary key of sitelicense_ip_address (v2.0.5 expects organization_id, organization_no)'
SELECT a.attname
  FROM pg_index i
  JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
 WHERE i.indrelid = 'sitelicense_ip_address'::regclass AND i.indisprimary
 ORDER BY a.attname;

\echo '== activities that are not finished (their temp_data is not converted; finish or cancel them first)'
SELECT activity_status, count(*) FROM workflow_activity
 WHERE activity_status NOT IN ('F', 'P', 'C') GROUP BY activity_status ORDER BY 1;

\echo '== file_onetime_download rows (W2025-29.sql drops and recreates the table; these rows are lost)'
SELECT count(*) AS file_onetime_download FROM file_onetime_download;

\echo '== stats_events (relkind p means already partitioned)'
SELECT c.relkind, (SELECT count(*) FROM stats_events) AS rows,
       (SELECT min(date) FROM stats_events) AS min_date,
       (SELECT max(date) FROM stats_events) AS max_date
  FROM pg_class c WHERE c.relname = 'stats_events';

\echo '== admin_settings names'
SELECT id, name FROM admin_settings ORDER BY id;

\echo '== restricted_access has secret_URL_file_download (W2025-29.sql needs it)'
SELECT name, settings ? 'secret_URL_file_download' AS has_secret_url
  FROM admin_settings WHERE name = 'restricted_access';

\echo '== admin_lang_settings'
SELECT lang_code, is_registered, sequence FROM admin_lang_settings ORDER BY sequence;

\echo '== counts to compare after the upgrade'
SELECT 'records_metadata' AS t, count(*) FROM records_metadata
UNION ALL SELECT 'pidstore recid registered', count(*) FROM pidstore_pid WHERE pid_type = 'recid' AND status = 'R'
UNION ALL SELECT 'item_type', count(*) FROM item_type
UNION ALL SELECT 'index', count(*) FROM index
UNION ALL SELECT 'accounts_user', count(*) FROM accounts_user
UNION ALL SELECT 'authors', count(*) FROM authors
UNION ALL SELECT 'files_files', count(*) FROM files_files
UNION ALL SELECT 'workflow_activity', count(*) FROM workflow_activity
UNION ALL SELECT 'stats_events', count(*) FROM stats_events
UNION ALL SELECT 'stats_aggregation', count(*) FROM stats_aggregation;
