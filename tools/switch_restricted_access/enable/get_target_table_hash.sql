SELECT *
FROM (
    SELECT 'item_type_name' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type_name
    ) t
    UNION ALL
    SELECT 'item_type' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type
    ) t
    UNION ALL
    SELECT 'item_type_mapping' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type_mapping
    ) t
    UNION ALL
    SELECT 'item_type_property' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type_property
    ) t
    UNION ALL
    SELECT 'accounts_role' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM accounts_role
    ) t
    UNION ALL
    SELECT 'index' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM index
    ) t
    UNION ALL
    SELECT 'workflow_flow_define' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_flow_define
    ) t
    UNION ALL
    SELECT 'workflow_flow_action' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_flow_action
    ) t
    UNION ALL
    SELECT 'workflow_workflow' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_workflow
    ) t
    UNION ALL
    SELECT 'workflow_userrole' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_userrole
    ) t
    UNION ALL
    SELECT 'mail_template_genres' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM mail_template_genres
    ) t
    UNION ALL
    SELECT 'mail_templates' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM mail_templates
    ) t
    UNION ALL
    SELECT 'admin_settings' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM admin_settings
    ) t
    UNION ALL
    SELECT 'item_type_edit_history' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type_edit_history
    ) t
    UNION ALL
    SELECT 'jsonld_mappings' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM jsonld_mappings
    ) t
    UNION ALL
    SELECT 'rocrate_mapping' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM rocrate_mapping
    ) t
    UNION ALL
    SELECT 'access_actionsroles' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM access_actionsroles
    ) t
    UNION ALL
    SELECT 'accounts_userrole' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM accounts_userrole
    ) t
    UNION ALL
    SELECT 'communities_community' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM communities_community
    ) t
    UNION ALL
    SELECT 'shibboleth_userrole' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM shibboleth_userrole
    ) t
    UNION ALL
    SELECT 'workflow_flow_action_role' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_flow_action_role
    ) t
    UNION ALL
    SELECT 'harvest_settings' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM harvest_settings
    ) t
    UNION ALL
    SELECT 'journal' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM journal
    ) t
    UNION ALL
    SELECT 'resync_indexes' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM resync_indexes
    ) t
    UNION ALL
    SELECT 'workflow_activity' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_activity
    ) t
    UNION ALL
    SELECT 'sword_clients' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM sword_clients
    ) t
    UNION ALL
    SELECT 'mail_template_users' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM mail_template_users
    ) t
    UNION ALL
    SELECT 'author_affiliation_community_relations' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM author_affiliation_community_relations
    ) t
    UNION ALL
    SELECT 'author_community_relations' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM author_community_relations
    ) t
    UNION ALL
    SELECT 'author_prefix_community_relations' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM author_prefix_community_relations
    ) t
    UNION ALL
    SELECT 'communities_community_record' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM communities_community_record
    ) t
    UNION ALL
    SELECT 'communities_featured_community' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM communities_featured_community
    ) t
    UNION ALL
    SELECT 'user_activity_logs' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM user_activity_logs
    ) t
    UNION ALL
    SELECT 'resync_logs' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM resync_logs
    ) t
    UNION ALL
    SELECT 'workflow_activity_action' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_activity_action
    ) t
) s
ORDER BY table_name;
