--#34071 location
ALTER TABLE public.files_location ADD COLUMN s3_endpoint_url varchar(128);
ALTER TABLE public.files_location ADD COLUMN s3_send_file_directly boolean NOT NULL DEFAULT true;

--#34072 activitylog
CREATE TABLE workflow_activity_count (
	status VARCHAR(1) NOT NULL,
	created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	date Date NOT NULL,
	activity_count Integer NOT NULL,
	PRIMARY KEY (date)
);
INSERT INTO workflow_activity_count (status,created,updated,date,activity_count) VALUES('N',now(),now(),CURRENT_DATE,(select count(*) from workflow_activity as a where a.created >= CURRENT_DATE and a.created < CURRENT_DATE + 1));

--#34073 reindex
SELECT setval('admin_settings_id_seq', (SELECT MAX(ID) FROM admin_settings));
insert into public.admin_settings(name,settings) values 
 ('elastic_reindex_settings','{"has_errored": false}')
;

