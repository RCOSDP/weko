CREATE TABLE workflow_activity_count (
	status VARCHAR(1) NOT NULL,
	created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	date Date NOT NULL,
	activity_count Integer NOT NULL,
	PRIMARY KEY (date)
);
INSERT INTO workflow_activity_count (status,created,updated,date,activity_count) VALUES('N',now(),now(),CURRENT_DATE,(select count(*) from workflow_activity as a where a.created >= CURRENT_DATE and a.created < CURRENT_DATE + 1;));