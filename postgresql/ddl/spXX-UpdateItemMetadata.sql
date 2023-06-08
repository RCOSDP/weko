-- (注意)tableデータのバックアップは必ずとること!
--1. weko_shared_id=-1,NULLのとき[]に変換
UPDATE public.item_metadata
SET json = json::jsonb  || jsonb_set(json, '{"shared_user_id"}'::text[], to_jsonb('[]'::text), false)::jsonb
WHERE json->>'shared_user_id' IS NULL OR json IS NULL;

UPDATE public.item_metadata
SET json = json  || jsonb_set(json, '{"shared_user_id"}'::text[], to_jsonb('[]'::text), false) 
WHERE json->>'shared_user_id' = '-1';

--2. weko_shared_id=-1,NULL以外[num]に変換
UPDATE public.item_metadata
SET json = json || jsonb_set(json, ('{"shared_user_id"}')::text[], to_jsonb(('['||(json->>'shared_user_id')||']')::text) ,false)
WHERE json->>'shared_user_id' <> '[]' AND json->>'shared_user_id' > '0';

--3. weko_shared_idsにコピー
UPDATE public.item_metadata SET json = json || jsonb_set(json, ('{"shared_user_ids"}')::text[], to_jsonb((json->>'shared_user_id')::text), true);

--4. weko_shared_idをjsonから削除
UPDATE public.item_metadata SET json = json - 'shared_user_id';