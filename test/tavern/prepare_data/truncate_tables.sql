-- truncate item_type_name, item_type, item_type_edit_history, jsonld_mappings,
-- rocrate_mapping, workflow_workflow, sword_clients, workflow_activity,
-- workflow_userrole, workflow_activity_action
TRUNCATE TABLE item_type_name CASCADE;

TRUNCATE TABLE item_type_mapping;

TRUNCATE TABLE item_type_mapping_version;

TRUNCATE TABLE item_type_version;

-- truncate workflow_flow_define, workflow_flow_action, workflow_workflow, workflow_activity,
-- sword_clients, workflow_flow_action_role, workflow_userrole, workflow_activity_action
TRUNCATE TABLE workflow_flow_define CASCADE;

TRUNCATE TABLE workflow_activity_count;

TRUNCATE TABLE workflow_action_history RESTART IDENTITY;

-- truncate pidstore_pid, pidrelations_pidrelation, pidstore_redirect
TRUNCATE TABLE pidstore_pid RESTART IDENTITY CASCADE;

-- truncate pidstore_recid, cris_linkage_result
TRUNCATE TABLE pidstore_recid CASCADE;

-- truncate records_metadata, communities_community_record, records_buckets
TRUNCATE TABLE records_metadata CASCADE;

TRUNCATE TABLE records_metadata_version;

-- truncate files_bucket, files_buckettags, files_multipartobject, files_object,
-- records_buckets, files_multipartobject_part, files_objecttags
TRUNCATE TABLE files_bucket CASCADE;

-- truncate files_files, files_multipartobject, files_object,
-- files_multipartobject_part, files_objecttags
TRUNCATE TABLE files_files CASCADE;

-- truncate item_metadata, cris_linkage_result
TRUNCATE TABLE item_metadata CASCADE;

TRUNCATE TABLE item_metadata_version;

-- truncate oauth2server_client, oauth2server_token, sword_clients
TRUNCATE TABLE oauth2server_client CASCADE;

TRUNCATE TABLE notifications_user_settings;

TRUNCATE TABLE authors;

-- reset workflow_activity_id_seq
SELECT setval('workflow_activity_id_seq', 1, false);

-- reset workflow_workflow
SELECT setval('workflow_workflow_id_seq', 1001, false);

-- reset pidstore_recid_id_seq
SELECT setval('public.pidstore_recid_recid_seq', 2000000, true);

-- reset item_type_name
SELECT setval('item_type_name_id_seq', 40001, false);

-- reset item_type
SELECT setval('item_type_id_seq', 40001, false);

-- reset item_type_mapping
SELECT setval('item_type_mapping_id_seq', 40001, false);

-- reset authors
SELECT setval('authors_id_seq', 1, false);