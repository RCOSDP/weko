ALTER TABLE files_location ADD COLUMN readonly_access_key CHARACTER VARYING(128);
ALTER TABLE files_location ADD COLUMN readonly_secret_key CHARACTER VARYING(128);