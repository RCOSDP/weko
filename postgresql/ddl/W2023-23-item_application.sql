-- public.workflow_activity_item_application definition
CREATE TABLE public.workflow_activity_item_application (
	status varchar(1) NOT NULL,
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	activity_id varchar(24) NOT NULL,
	item_application jsonb NULL,
	display_item_application_button bool NOT NULL,
	CONSTRAINT pk_workflow_activity_item_application PRIMARY KEY (id)
);
CREATE INDEX ix_workflow_activity_item_application_activity_id ON public.workflow_activity_item_application USING btree (activity_id);

-- public.item_application definition
CREATE TABLE public.item_application (
	created timestamp NOT NULL,
	updated timestamp NOT NULL,
	id serial4 NOT NULL,
	item_id uuid NOT NULL,
	item_application jsonb NULL,
	CONSTRAINT pk_item_application PRIMARY KEY (id)
);