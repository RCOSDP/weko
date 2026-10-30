-- Prepares data that postgresql/ddl/W2025-29.sql assumes but a v0.9.20
-- database does not have.
BEGIN;

-- W2025-29.sql creates mailtype with the values 'recipient', 'cc', 'bcc',
-- but SQLAlchemy stores the member names of MailType (db.Enum(MailType)),
-- as the alembic revision b1495e98969b does. W2025-29.sql skips the type
-- when it exists, so create it with the names first.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
         WHERE n.nspname = current_schema() AND t.typname = 'mailtype'
    ) THEN
        CREATE TYPE mailtype AS ENUM ('RECIPIENT', 'CC', 'BCC');
    END IF;
END$$;

-- W2025-29.sql adds max_* keys to restricted_access with
-- jsonb_set(settings, '{secret_URL_file_download}',
--          settings->'secret_URL_file_download' || ...).
-- Without the key the expression is NULL and the whole settings becomes
-- NULL, so add the v2.0.5 defaults (WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS)
-- for the keys that are missing.
UPDATE admin_settings
   SET settings = jsonb_build_object(
        'secret_URL_file_download', jsonb_build_object(
            'secret_expiration_date', 30,
            'max_secret_expiration_date', 30,
            'secret_expiration_date_unlimited_chk', false,
            'secret_download_limit', 10,
            'max_secret_download_limit', 10,
            'secret_download_limit_unlimited_chk', false),
        'content_file_download', jsonb_build_object(
            'expiration_date', 30,
            'expiration_date_unlimited_chk', false,
            'download_limit', 10,
            'download_limit_unlimited_chk', false)
       ) || settings
 WHERE name = 'restricted_access'
   AND NOT (settings ? 'secret_URL_file_download' AND settings ? 'content_file_download');

COMMIT;
