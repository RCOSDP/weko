--------------------------------------------------------------------------------
-- public.files_multipartobject_part のレイアウト変更
--   注意！！：テーブルに依存するオブジェクト（ビューなど）が削除される場合があります。それらのオブジェクトは復元されません。
--   2023/11/15 
--------------------------------------------------------------------------------


-- 新テーブルの作成
create table public."$$files_multipartobject_part" (
  created timestamp(6) without time zone not null
  , updated timestamp(6) without time zone not null
  , upload_id uuid not null
  , part_number integer not null
  , checksum character varying(255)
  , etag character varying(255)
)
/


-- 新テーブルへデータ投入
insert into public."$$files_multipartobject_part"(created, updated, upload_id, part_number, checksum)
  select org.created, org.updated, org.upload_id, org.part_number, org.checksum from public.files_multipartobject_part org
/


-- 元テーブルの削除
drop table public.files_multipartobject_part cascade
/


-- 新テーブルをリネームして元テーブル名に変更
alter table public."$$files_multipartobject_part" rename to files_multipartobject_part
/


-- 主キーの作成
alter table public.files_multipartobject_part  add constraint pk_files_multipartobject_part primary key (upload_id,part_number)
/


-- コメントの作成
comment on table public.files_multipartobject_part is ''
/

comment on column public.files_multipartobject_part.created is ''
/

comment on column public.files_multipartobject_part.updated is ''
/

comment on column public.files_multipartobject_part.upload_id is ''
/

comment on column public.files_multipartobject_part.part_number is ''
/

comment on column public.files_multipartobject_part.checksum is ''
/

comment on column public.files_multipartobject_part.etag is ''
/


-- 外部キーの作成
alter table public.files_multipartobject_part
  add constraint fk_files_multipartobject_part_upload_id_files_multipartobject  foreign key (upload_id)
  references public.files_multipartobject(upload_id)
/


-- その他のDDL
grant DELETE on public.files_multipartobject_part to "invenio"
/

grant INSERT on public.files_multipartobject_part to "invenio"
/

grant REFERENCES on public.files_multipartobject_part to "invenio"
/

grant SELECT on public.files_multipartobject_part to "invenio"
/

grant TRIGGER on public.files_multipartobject_part to "invenio"
/

grant TRUNCATE on public.files_multipartobject_part to "invenio"
/

grant UPDATE on public.files_multipartobject_part to "invenio"
/

