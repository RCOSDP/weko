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

-- truncate authors, author_community_relations
TRUNCATE TABLE authors CASCADE;

-- truncate index, communities_community, harvest_settings, journal,
-- resync_indexes, author_affiliation_community_relations,
-- author_community_relations, author_prefix_community_relations,
-- communities_community_relations, communities_featured_community,
-- resync_logs, user_activity_logs
TRUNCATE TABLE index CASCADE;

TRUNCATE TABLE oaiserver_schema;

TRUNCATE TABLE pdfcoverpage_set;

-- truncate accounts_role, access_actionsroles, accounts_userrole,
-- communities_community, shibboleth_userrole, workflow_flow_action_role,
-- workflow_userrole, author_affiliation_community_relations,
-- author_community_relations, author_prefix_community_relations,
-- communities_community_record, communities_featured_community,
-- user_activity_logs
TRUNCATE TABLE accounts_role RESTART IDENTITY CASCADE;

TRUNCATE TABLE oaiserver_set;

TRUNCATE TABLE oaiserver_identify;

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

-- reset access_actionsroles
SELECT setval('access_actionsroles_id_seq', 1, false);
