-- for weko#23307
CREATE TABLE public.workflow_userrole (
    status varchar(1) NOT NULL,
    created timestamp NOT NULL,
    updated timestamp NOT NULL,
    workflow_id int4 NOT NULL,
    role_id int4 NOT NULL,
    CONSTRAINT pk_workflow_userrole PRIMARY KEY (workflow_id, role_id)
);
ALTER TABLE public.workflow_userrole ADD CONSTRAINT fk_workflow_userrole_role_id_accounts_role FOREIGN KEY (role_id) REFERENCES accounts_role(id) ON DELETE CASCADE;
ALTER TABLE public.workflow_userrole ADD CONSTRAINT fk_workflow_userrole_workflow_id_workflow_workflow FOREIGN KEY (workflow_id) REFERENCES workflow_workflow(id) ON DELETE CASCADE;
