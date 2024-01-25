ALTER TABLE mail_config ADD COLUMN  mail_local_hostname character varying(255) DEFAULT '';
UPDATE authors SET json=(json#>> '{}')::jsonb;
