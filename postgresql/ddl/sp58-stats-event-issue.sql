-- weko#25316
ALTER TABLE stats_events ADD CONSTRAINT uq_stats_key_stats_events UNIQUE (source_id, index);
ALTER TABLE stats_aggregation ADD CONSTRAINT uq_stats_key_stats_aggregation UNIQUE (source_id, index);
ALTER TABLE stats_bookmark ADD CONSTRAINT uq_stats_key_stats_bookmark UNIQUE (source_id, index);
