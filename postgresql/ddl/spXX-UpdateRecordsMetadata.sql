-- (注意)tableデータのバックアップは必ずとること!
--1. weko_shared_id=-1,NULLのとき[]に変換
UPDATE records_metadata
SET json = json || jsonb_set(json, '{"weko_shared_id"}'::text[], to_jsonb('[]'::text), false) 
WHERE json->>'weko_shared_id' IS NULL OR json IS NULL;;

UPDATE records_metadata
SET json = json || jsonb_set(json, '{"weko_shared_id"}'::text[], to_jsonb('[]'::text), false) 
WHERE json->>'weko_shared_id' = '-1';

--2. weko_shared_id=-1,NULL以外[num]に変換
UPDATE records_metadata
SET json = json || jsonb_set(json, ('{"weko_shared_id"}')::text[], to_jsonb(('['||(json->>'weko_shared_id')||']')::text), false)
WHERE json->>'weko_shared_id' <> '[]'  AND json->>'weko_shared_id' > '0';

--3. weko_shared_idsにコピー
UPDATE records_metadata
SET json = json || jsonb_set(json, ('{"weko_shared_ids"}'), (json->>'weko_shared_id'), false);

--4. weko_shared_idをjsonから削除
UPDATE records_metadata SET json = json - 'weko_shared_id';