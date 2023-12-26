-- public.workflow_activity_request_mail definition
CREATE TABLE public.workflow_activity_request_mail (
	status varchar(1) NOT NULL,
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	activity_id varchar(24) NOT NULL,
	request_maillist jsonb NULL,
	display_request_button bool NOT NULL,
	CONSTRAINT pk_workflow_activity_request_mail PRIMARY KEY (id)
);
CREATE INDEX ix_workflow_activity_request_mail_activity_id ON public.workflow_activity_request_mail USING btree (activity_id);

-- public.request_mail_list definition
CREATE TABLE public.request_mail_list (
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	item_id uuid NOT NULL,
	mail_list jsonb NULL,
	CONSTRAINT pk_request_mail_list PRIMARY KEY (id)
);

-- public.workflow_flow_action_role definition
ALTER TABLE public.workflow_flow_action_role ADD action_request_mail Boolean NOT NULL DEFAULT false;