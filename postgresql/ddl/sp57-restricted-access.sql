-- weko#24326
-- weko#24327
-- weko#24328
-- weko#24951

-- file_onetime_download table
alter table file_onetime_download
    add extra_info jsonb;
-- guest_activity table
alter table guest_activity
    add expiration_date integer;
alter table guest_activity
    add is_usage_report boolean;
-- workflow_action_history table
alter table workflow_action_history
    add action_order integer;
-- workflow_activity table
alter table workflow_activity
    add action_order integer;
-- workflow_activity_action table
alter table workflow_activity_action
    add action_order integer;
-- workflow_flow_action table
alter table workflow_flow_action
    add send_mail_setting jsonb;
-- workflow_flow_action_role table
alter table workflow_flow_action_role
    add specify_property varchar(255);
