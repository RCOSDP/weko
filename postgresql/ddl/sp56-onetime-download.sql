-- weko#24695
-- weko#23888
-- weko#24088
-- weko#24089
-- weko#24080
-- weko#24325
-- workflow_activity table
alter table workflow_activity
    add approval1 text;
alter table workflow_activity
    add approval2 text;
alter table workflow_activity
    add extra_info jsonb;
-- workflow_workflow table
alter table workflow_workflow
    add open_restricted boolean default true not null;
-- file_permission table
alter table file_permission
    add usage_report_activity_id varchar(255);
-- file_onetime_download table
create table file_onetime_download
(
    created         timestamp    not null,
    updated         timestamp    not null,
    id              serial       not null
        constraint pk_file_onetime_download
            primary key,
    file_name       varchar(255) not null,
    user_mail       varchar(255) not null,
    record_id       varchar(255) not null,
    download_count  integer      not null,
    expiration_date integer      not null
);
-- guest_activity
create table guest_activity
(
    created     timestamp    not null,
    updated     timestamp    not null,
    id          serial       not null
        constraint pk_guest_activity
            primary key,
    user_mail   varchar(255) not null,
    record_id   varchar(255) not null,
    file_name   varchar(255) not null,
    activity_id varchar(24)  not null,
    token       varchar(255) not null
);
