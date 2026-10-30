-- Read-only checks after the upgrade. Compare the counts with the
-- preflight output saved before the upgrade.
\pset footer off
\echo '== applied steps'
SELECT step, done_at FROM weko_upgrade_v205_steps ORDER BY done_at;

\echo '== stats_events is partitioned (relkind p) and its partitions'
SELECT relkind FROM pg_class WHERE relname = 'stats_events';
SELECT min(c.relname) AS first_partition, max(c.relname) AS last_partition, count(*) AS partitions
  FROM pg_inherits i JOIN pg_class c ON c.oid = i.inhrelid
 WHERE i.inhparent = 'stats_events'::regclass;

\echo '== user_activity_logs partitions'
SELECT min(c.relname) AS first_partition, max(c.relname) AS last_partition, count(*) AS partitions
  FROM pg_inherits i JOIN pg_class c ON c.oid = i.inhrelid
 WHERE i.inhparent = 'user_activity_logs'::regclass;

\echo '== mailtype labels (expected RECIPIENT, CC, BCC)'
SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid
 WHERE t.typname = 'mailtype' ORDER BY e.enumsortorder;

\echo '== admin_settings that must not be NULL'
SELECT name, settings IS NULL AS is_null FROM admin_settings
 WHERE name IN ('restricted_access', 'site_license_mail_settings', 'elastic_reindex_settings')
 ORDER BY name;

\echo '== default item types and their jsonld mappings'
SELECT t.id, t.is_deleted, j.id AS jsonld_mapping
  FROM item_type t LEFT JOIN jsonld_mappings j ON j.item_type_id = t.id
 WHERE t.id IN (15, 16, 30001, 30002) ORDER BY t.id;

\echo '== records still holding the old owner keys (expected 0)'
SELECT count(*) AS old_owner_keys FROM records_metadata
 WHERE json ? 'weko_shared_id' AND NOT json ? 'weko_shared_ids';

\echo '== counts to compare with the preflight output'
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
