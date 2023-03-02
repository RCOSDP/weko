--facet_search_setting テーブルへのカラム追加
ALTER TABLE facet_search_setting ADD COLUMN IS_OPEN boolean DEFAULT true NOT NULL;
ALTER TABLE facet_search_setting ADD COLUMN UI_TYPE character varying(20) DEFAULT 'Editbox' NOT NULL;
ALTER TABLE facet_search_setting ADD COLUMN DISPLAY_NUMBER integer;
--対象時期を範囲指定UI へ変更
update facet_search_setting set UI_TYPE = 'Range' where mapping = 'temporal';
commit;