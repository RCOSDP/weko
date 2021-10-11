-- weko#28168
--- Get path of license and keep datas.
WITH license AS (
    SELECT
        ( '{detail_condition, ' || idx - 1 || '}' ) :: TEXT [] AS PATH,
        ( '{' || idx - 1 || '}' ) :: TEXT [] AS PATH_SEARCH,
        detail_condition ->> 'mappingFlg' AS mappingFlg,
        detail_condition ->> 'mappingName' AS mappingName,
        detail_condition ->> 'useable_status' AS useable_status,
        detail_condition ->> 'default_display' AS default_display 
    FROM
        "search_management",
        jsonb_array_elements ( search_setting_all -> 'detail_condition' ) WITH ORDINALITY arr ( detail_condition, idx ) 
    WHERE
        detail_condition ->> 'id' = 'license' 
    )
--- Update license data.
UPDATE search_management 
    SET search_setting_all = jsonb_set (
        search_setting_all,
        license.PATH,
        ( '{
            "id": "license",
            "mapping": [],
            "contents": "License",
            "inputVal": "",
            "check_val": [
            {
            "id": "license_12",
            "contents": "CC0" 
            },
            {
            "id": "license_6",
            "contents": "CC BY 3.0" 
            },
            {
            "id": "license_7",
            "contents": "CC BY-SA 3.0" 
            },
            {
            "id": "license_8",
            "contents": "CC BY-ND 3.0" 
            },
            {
            "id": "license_9",
            "contents": "CC BY-NC 3.0" 
            },
            {
            "id": "license_10",
            "contents": "CC BY-NC-SA 3.0" 
            },
            {
            "id": "license_11",
            "contents": "CC BY-NC-ND 3.0" 
            },
            {
            "id": "license_0",
            "contents": "CC BY 4.0" 
            },
            {
            "id": "license_1",
            "contents": "CC BY-SA 4.0" 
            },
            {
            "id": "license_2",
            "contents": "CC BY-ND 4.0" 
            },
            {
            "id": "license_3",
            "contents": "CC BY-NC 4.0" 
            },
            {
            "id": "license_4",
            "contents": "CC BY-NC-SA 4.0" 
            },
            {
            "id": "license_5",
            "contents": "CC BY-NC-ND 4.0" 
            },
            {
            "id": "license_free",
            "contents": "Other" 
            }
            ],
            "inputType": "checkbox_list",
            "mappingFlg": ' || license.mappingFlg || ',
            "mappingName": "' || license.mappingName || '",
            "useable_status": ' || license.useable_status || ',
            "default_display": ' || license.default_display || '
        }' ) :: jsonb,
    FALSE 
    ),
    search_conditions = jsonb_set (
        search_conditions,
        license.PATH_SEARCH,
        ( '{
            "id": "license",
            "mapping": [],
            "contents": "License",
            "inputVal": "",
            "check_val": [
            {
            "id": "license_12",
            "contents": "CC0" 
            },
            {
            "id": "license_6",
            "contents": "CC BY 3.0" 
            },
            {
            "id": "license_7",
            "contents": "CC BY-SA 3.0" 
            },
            {
            "id": "license_8",
            "contents": "CC BY-ND 3.0" 
            },
            {
            "id": "license_9",
            "contents": "CC BY-NC 3.0" 
            },
            {
            "id": "license_10",
            "contents": "CC BY-NC-SA 3.0" 
            },
            {
            "id": "license_11",
            "contents": "CC BY-NC-ND 3.0" 
            },
            {
            "id": "license_0",
            "contents": "CC BY 4.0" 
            },
            {
            "id": "license_1",
            "contents": "CC BY-SA 4.0" 
            },
            {
            "id": "license_2",
            "contents": "CC BY-ND 4.0" 
            },
            {
            "id": "license_3",
            "contents": "CC BY-NC 4.0" 
            },
            {
            "id": "license_4",
            "contents": "CC BY-NC-SA 4.0" 
            },
            {
            "id": "license_5",
            "contents": "CC BY-NC-ND 4.0" 
            },
            {
            "id": "license_free",
            "contents": "Other" 
            }
            ],
            "inputType": "checkbox_list",
            "mappingFlg": ' || license.mappingFlg || ',
            "mappingName": "' || license.mappingName || '",
            "useable_status": ' || license.useable_status || ',
            "default_display": ' || license.default_display || '
        }' ) :: jsonb,
    FALSE 
    ) 
FROM
    license;
