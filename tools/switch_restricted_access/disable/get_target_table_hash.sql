SELECT *
FROM (
    SELECT 'item_type' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type
    ) t
    UNION ALL
    SELECT 'item_type_property' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM item_type_property
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
    SELECT 'workflow_activity_action' AS table_name,
        md5(STRING_AGG(t::text, ',' ORDER BY t::text)) AS hash
    FROM (
        SELECT * FROM workflow_activity_action
    ) t
) s
ORDER BY table_name;
