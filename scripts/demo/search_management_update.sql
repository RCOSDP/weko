DO $$
DECLARE
    rec RECORD;
    accessrights_json jsonb := '{
        "id":"accessrights",
        "contents":"",
        "contents_value":{"en":"Access Rights","ja":"アクセス権"},
        "useable_status":true,
        "mapping":["embargoed access","metadata only access","open access","restricted access"],
        "check_val":[
            {"id":"embargoed access","contents":"embargoed access","checkStus":false},
            {"id":"metadata only access","contents":"metadata only access","checkStus":false},
            {"id":"open access","contents":"open access","checkStus":false},
            {"id":"restricted access","contents":"restricted access","checkStus":false}
        ],
        "default_display":true,
        "inputType":"checkbox_list",
        "inputVal":"",
        "mappingFlg":false,
        "mappingName":""
    }'::jsonb;
BEGIN
    FOR rec IN SELECT id, search_conditions, search_setting_all FROM search_management LOOP
        -- search_conditions
        IF rec.search_conditions IS NOT NULL THEN
            IF NOT EXISTS (
                SELECT 1 FROM jsonb_array_elements(rec.search_conditions) elem
                WHERE elem->>'id' = 'accessrights'
            ) THEN
                UPDATE search_management SET search_conditions = rec.search_conditions || accessrights_json WHERE id = rec.id;
            END IF;
        END IF;
        -- search_setting_all
        IF rec.search_setting_all IS NOT NULL AND rec.search_setting_all->'detail_condition' IS NOT NULL THEN
            IF NOT (rec.search_setting_all->'detail_condition')::jsonb @> '[{"id": "accessrights"}]'::jsonb THEN
                UPDATE search_management SET search_setting_all = jsonb_set(
                    rec.search_setting_all,
                    '{detail_condition}',
                    (rec.search_setting_all->'detail_condition')::jsonb || accessrights_json
                ) WHERE id = rec.id;
            END IF;
        END IF;
    END LOOP;
END $$;
