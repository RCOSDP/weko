--------------------------------------------------------------------------------
-- public.files_multipartobject のレイアウト変更
--   注意！！：テーブルに依存するオブジェクト（ビューなど）が削除される場合があります。それらのオブジェクトは復元されません。
--   2023/11/15 
--------------------------------------------------------------------------------


-- 新テーブルの作成
create table public."$$files_multipartobject" (
  created timestamp(6) without time zone not null
  , updated timestamp(6) without time zone not null
  , upload_id uuid not null
  , bucket_id uuid
  , key text
  , file_id uuid not null
  , chunk_size integer
  , size bigint
  , completed boolean not null
  , created_by_id integer
)
/


-- 新テーブルへデータ投入
insert into public."$$files_multipartobject"(created, updated, upload_id, bucket_id, key, file_id, chunk_size, size, completed, created_by_id)
  select org.created, org.updated, org.upload_id, org.bucket_id, org.key, org.file_id, org.chunk_size, org.size, org.completed, NULL from public.files_multipartobject org
/


-- 元テーブルの削除
drop table public.files_multipartobject cascade
/


-- 新テーブルをリネームして元テーブル名に変更
alter table public."$$files_multipartobject" rename to files_multipartobject
/


-- インデックスとユニーク制約の作成
create unique index uix_item on public.files_multipartobject(upload_id,bucket_id,key)
/

alter table public.files_multipartobject add constraint uix_item unique (upload_id,bucket_id,key)
/


-- 主キーの作成
alter table public.files_multipartobject  add constraint pk_files_multipartobject primary key (upload_id)
/


-- コメントの作成
comment on table public.files_multipartobject is ''
/

comment on column public.files_multipartobject.created is ''
/

comment on column public.files_multipartobject.updated is ''
/

comment on column public.files_multipartobject.upload_id is ''
/

comment on column public.files_multipartobject.bucket_id is ''
/

comment on column public.files_multipartobject.key is ''
/

comment on column public.files_multipartobject.file_id is ''
/

comment on column public.files_multipartobject.chunk_size is ''
/

comment on column public.files_multipartobject.size is ''
/

comment on column public.files_multipartobject.completed is ''
/

comment on column public.files_multipartobject.created_by_id is ''
/


-- 外部キーの作成
alter table public.files_multipartobject
  add constraint fk_files_multipartobject_bucket_id_files_bucket  foreign key (bucket_id)
  references public.files_bucket(id)
/

alter table public.files_multipartobject
  add constraint fk_files_multipartobject_created_by_id_accounts_user  foreign key (created_by_id)
  references public.accounts_user(id)
/

alter table public.files_multipartobject
  add constraint fk_files_multipartobject_file_id_files_files  foreign key (file_id)
  references public.files_files(id)
/

alter table public.files_multipartobject_part
  add constraint fk_files_multipartobject_part_upload_id_files_multipartobject  foreign key (upload_id)
  references public.files_multipartobject(upload_id)
/


-- その他のDDL
grant DELETE on public.files_multipartobject to "invenio"
/

grant INSERT on public.files_multipartobject to "invenio"
/

grant REFERENCES on public.files_multipartobject to "invenio"
/

grant SELECT on public.files_multipartobject to "invenio"
/

grant TRIGGER on public.files_multipartobject to "invenio"
/

grant TRUNCATE on public.files_multipartobject to "invenio"
/

grant UPDATE on public.files_multipartobject to "invenio"
/

