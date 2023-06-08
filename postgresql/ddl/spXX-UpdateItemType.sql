/*
 * (注意)tableデータのバックアップは必ずとること!
 */
-- schema add roles
UPDATE 
    public.item_type
SET 
    schema = schema || jsonb_set( schema, ('{"properties","'||COND.meta_keys||'","items","properties","roles"}')::text[], ('{"type": "array","items": {"type": "object","format": "object","properties": {"role": {"type": ["null","string"],"title": "ロール","format": "select","currentEnum": []}}},"title": "ロール","format": "array"}')::jsonb, true)
FROM 
    (
        SELECT T.keys meta_keys, T.props, T.ID AS innerId
        FROM
        (
            SELECT jsonb_object_keys(schema->'properties') keys, schema->'properties' props, id
            FROM public.item_type
        ) AS T
        WHERE T.keys LIKE 'item_%'
        AND T.props->T.keys->>'type' = 'array'
        AND T.props->T.keys->'items'->>'type' = 'object'
        AND T.props->T.keys->'items'->'properties' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'url' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'terms' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'format' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'groups' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'provide' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'version' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'dataType' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'fileDate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filename' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filesize' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessdate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessrole' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'displaytype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensefree' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensetype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'termsDescription' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'role' IS NULL
        ) AS COND
WHERE id = COND.innerId;
-- schema delete groups
UPDATE 
    public.item_type
SET
    schema = schema || jsonb_set( schema, ('{"properties","'||COND.meta_keys||'","items","properties"}')::text[], ((schema->'properties'->COND.meta_keys->'items'->'properties')::jsonb - 'groups'), false)
FROM 
    (
        SELECT T.keys meta_keys, T.props, T.id AS innerId
        FROM
        (
            SELECT jsonb_object_keys(T.schema->'properties')  keys, T.schema->'properties' props, id
            FROM public.item_type
        ) AS T
        WHERE T.keys LIKE 'item_%'
        AND T.props->T.keys->>'type' = 'array'
        AND T.props->T.keys->'items'->>'type' = 'object'
        AND T.props->T.keys->'items'->'properties' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'url' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'terms' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'format' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'groups' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'provide' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'version' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'dataType' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'fileDate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filename' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filesize' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessdate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessrole' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'displaytype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensefree' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensetype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'termsDescription' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'role' IS NULL
        ) AS COND
WHERE id = COND.innerId;
-- schema delete dataType
-- TODO:

--form add roles 
WITH
    update_keys AS (
        SELECT T.keys AS meta_keys, T.id
        FROM
        (
            SELECT jsonb_object_keys(schema->'properties') keys, schema->'properties' props, id 
            FROM public.item_type
        ) AS T
        WHERE T.keys LIKE 'item_%'
        AND T.props->T.keys->>'type' = 'array'
        AND T.props->T.keys->'items'->>'type' = 'object'
        AND T.props->T.keys->'items'->'properties' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'url' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'terms' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'format' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'groups' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'provide' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'version' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'dataType' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'fileDate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filename' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filesize' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessdate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessrole' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'displaytype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensefree' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensetype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'termsDescription' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'role' IS NULL
    ),
    chosen_plans_json AS (
        SELECT
            id,
            t.chosen_plan,
            t.idx
        FROM
            public.item_type AS BASE,
            LATERAL
                jsonb_array_elements(BASE.form)
                WITH ORDINALITY AS t(chosen_plan, idx)
    ),
    chosen_plans AS (
        SELECT
          RECORD.id,
          RECORD.idx,
          RECORD.chosen_plan->>'key' AS key,
          RECORD.chosen_plan->>'items' AS items
        FROM
          chosen_plans_json AS RECORD
          INNER JOIN update_keys AS UPD
          ON RECORD.chosen_plan->>'key'=UPD.meta_keys AND RECORD.id=UPD.id
    )
UPDATE public.item_type AS BT
SET form = form || jsonb_set(form, ('{'||(CT.idx-1)::int||',"items", 0}')::text[], ('{"add":"New","key":"'||CT.key||'[].roles","items":[{"key":"'||CT.key||'[].roles[].role","type":"select","title":"ロール","titleMap":[],"title_i18n":{"en":"Role","ja":"ロール"}}],"style": {"add":"btn-success"},"title":"ロール","titleMap":[],"condition":"model.'||CT.key||'[arrayIndex].accessrole==''open_date''||model.'||CT.key||'[arrayIndex].accessrole==''open_login''","title_i18n":{"en":"Role","ja":"ロール"}}')::jsonb, true)
FROM chosen_plans AS CT
WHERE CT.id = BT.id;
-- form delete groups
WITH
    update_keys AS (
        SELECT T.keys AS meta_keys, T.id
        FROM
        (
            SELECT jsonb_object_keys(schema->'properties') keys, schema->'properties' props, id 
            FROM public.item_type
        ) AS T
        WHERE T.keys LIKE 'item_%'
        AND T.props->T.keys->>'type' = 'array'
        AND T.props->T.keys->'items'->>'type' = 'object'
        AND T.props->T.keys->'items'->'properties' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'url' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'terms' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'format' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'groups' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'provide' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'version' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'dataType' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'fileDate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filename' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filesize' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessdate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessrole' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'displaytype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensefree' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensetype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'termsDescription' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'role' IS NULL
    ),
    chosen_plans_json AS (
        SELECT
            id,
            t.chosen_plan,
            t.idx
        FROM
            public.item_type AS BASE,
            LATERAL
                jsonb_array_elements(BASE.form)
                WITH ORDINALITY AS t(chosen_plan, idx)
    ),
    chosen_plans AS (
        SELECT
          RECORD.id,
          RECORD.idx,
          RECORD.chosen_plan->>'key' AS key,
          RECORD.chosen_plan->'items' AS items
        FROM
          chosen_plans_json AS RECORD
          INNER JOIN update_keys AS UPD
          ON RECORD.chosen_plan->>'key'=UPD.meta_keys AND RECORD.id=UPD.id
    ),
    chosen_items_json AS (
        SELECT
            CP.id,
            CP.idx,
            CP.key,
            k.idx AS item_idx,
            k.item
        FROM
            chosen_plans AS CP,
            LATERAL
                jsonb_array_elements(CP.items)
                WITH ORDINALITY AS k(item, idx)
        WHERE
            CP.items->0 IS NOT NULL
    ),
    delete_target_items AS (
        SELECT *
        FROM chosen_items_json
        WHERE item->>'key' = key||'[].groups'
    )
UPDATE public.item_type AS BT
SET form = form || jsonb_set(form, ('{'||(DTI.idx-1)::int||',"items"}')::text[], (BT.form->(DTI.idx-1)::int->'items')::jsonb - (DTI.item_idx-1::int)::int, false)
FROM delete_target_items AS DTI
WHERE DTI.id = BT.id;
-- schema delete dataType
-- TODO:

-- render add roles
WITH
    update_keys AS (
        SELECT T.keys AS meta_keys, T.id
        FROM
        (
            SELECT jsonb_object_keys(schema->'properties') keys, schema->'properties' props, id 
            FROM public.item_type
        ) AS T
        WHERE T.keys LIKE 'item_%'
        AND T.props->T.keys->>'type' = 'array'
        AND T.props->T.keys->'items'->>'type' = 'object'
        AND T.props->T.keys->'items'->'properties' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'url' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'terms' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'format' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'groups' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'provide' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'version' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'dataType' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'fileDate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filename' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'filesize' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessdate' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'accessrole' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'displaytype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensefree' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'licensetype' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'termsDescription' IS NOT NULL
        AND T.props->T.keys->'items'->'properties'->'role' IS NULL
    )
UPDATE public.item_type AS BT
SET render = render || jsonb_set(render, 
                                ('{"schemaeditor", "schema", "'||UK.meta_keys||'", "properties", "roles"}')::text[], 
                                ('{
                                    "type": "array",
                                    "items": {
                                      "type": "object",
                                      "format": "object",
                                      "properties": {
                                        "role": {
                                          "enum": [],
                                          "type": [
                                            "null",
                                            "string"
                                          ],
                                          "title": "ロール",
                                          "format": "select",
                                          "currentEnum": []
                                        }
                                      }
                                    },
                                    "title": "ロール",
                                    "format": "array"
                                  }')::jsonb,
                                  true)
FROM update_keys AS UK
WHERE BT.id=UK.id;
-- render delete groups
-- TODO:
-- schema delete dataType
-- TODO:

-- table_row_map > schema > properties > item_xxxxx(UK.meta_keys) > items > properties > roles追加
' 以下の記述を追加
              "roles": {
                "type": "array",
                "items": {
                  "type": "object",
                  "format": "object",
                  "properties": {
                    "role": {
                      "type": [
                        "null",
                        "string"
                      ],
                      "title": "ロール",
                      "format": "select",
                      "currentEnum": []
                    }
                  },
                  "title": "ロール",
                  "format": "array"
                },
'
-- table_row_map > schema > properties > item_xxxxx(UK.meta_keys) > items > properties > groups削除
--TODO:
-- table_row_map > schema > properties > item_xxxxx(UK.meta_keys) > items > properties > dataType削除
--TODO:
