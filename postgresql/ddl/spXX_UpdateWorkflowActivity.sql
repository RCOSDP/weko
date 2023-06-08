--RENAME COLUMN
ALTER TABLE public.workflow_activity RENAME shared_user_id TO shared_user_ids;

--CHANGE COLUMN TYPE 1
ALTER TABLE public.workflow_activity
ALTER COLUMN shared_user_ids TYPE varchar(10) USING shared_user_ids::varchar(10);

--UPDATE EXIST RECODE
UPDATE public.workflow_activity SET shared_user_ids = '{'||shared_user_ids||'}'
UPDATE public.workflow_activity SET shared_user_ids = '{}' WHERE shared_user_ids = '{-1}' OR shared_user_ids IS NULL

--CHANGE COLUMN TYPE 2
ALTER TABLE public.workflow_activity
ALTER COLUMN shared_user_ids TYPE varchar(10)[] USING shared_user_ids::varchar(10)[]

--CHANGE COLUMN TYPE 3
ALTER TABLE public.workflow_activity
ALTER COLUMN shared_user_ids TYPE integer[] USING shared_user_ids::integer[]
