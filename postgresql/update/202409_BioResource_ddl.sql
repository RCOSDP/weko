ALTER TABLE facet_search_setting ADD COLUMN search_condition character varying(3) DEFAULT 'OR' NOT NULL;
ALTER TABLE resync_indexes ALTER COLUMN saving_format TYPE character varying(20);