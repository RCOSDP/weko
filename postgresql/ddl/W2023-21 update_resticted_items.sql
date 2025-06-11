-- public.file_secret_download definition
CREATE TABLE public.file_secret_download (
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	file_name varchar(255) NOT NULL,
	user_mail varchar(255) NOT NULL,
	record_id varchar(255) NOT NULL,
	download_count int4 NOT NULL,
	expiration_date int4 NOT NULL,
	CONSTRAINT pk_file_secret_download PRIMARY KEY (id)
);

-- 1. Add "shared_user_ids" column into workflow_activity table
ALTER TABLE
	workflow_activity
ADD
	shared_user_ids jsonb NULL;

-- 2. Update "shared_user_ids" with "shared_user_id column"
UPDATE
	workflow_activity
SET
	shared_user_ids = json_build_array(json_build_object('user', shared_user_id))
WHERE
	shared_user_ids IS NULL
	AND (
		shared_user_id IS NOT NULL
		AND shared_user_id > 0
	);

--3. Drop "shared_user_id" column
ALTER TABLE
	workflow_activity DROP COLUMN shared_user_id;