-- Converts stats_events into the RANGE (date) partitioned table of v2.0.5
-- (invenio_stats/models.py) and changes the primary keys of
-- stats_aggregation and stats_bookmark to (id, date). No script in the
-- repository does this.
--
-- Partitions are named stats_events_YYYYMM, as make_stats_events_partition_table
-- names them, and cover every month from January of the oldest event's year
-- to December of next year. The old table is dropped at the end, because the
-- CLI lists partitions with "tablename LIKE 'stats_events_%'".
-- Skipped when stats_events is already partitioned.
BEGIN;

DO $$
DECLARE
    first_month DATE;
    last_month DATE;
    m DATE;
    moved BIGINT;
    old_rows BIGINT;
    r RECORD;
BEGIN
    IF (SELECT relkind FROM pg_class
         WHERE relname = 'stats_events' AND relnamespace = current_schema()::regnamespace) = 'p' THEN
        RAISE NOTICE 'stats_events is already partitioned, skipping';
        RETURN;
    END IF;

    -- Free the constraint and index names for the new table.
    ALTER TABLE stats_events RENAME TO stats_events_before_v205;
    FOR r IN SELECT conname FROM pg_constraint
              WHERE conrelid = 'stats_events_before_v205'::regclass LOOP
        EXECUTE format('ALTER TABLE stats_events_before_v205 RENAME CONSTRAINT %I TO %I',
                       r.conname, r.conname || '_before_v205');
    END LOOP;
    FOR r IN SELECT c.relname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
              WHERE i.indrelid = 'stats_events_before_v205'::regclass
                AND c.relname NOT LIKE '%\_before\_v205' LOOP
        EXECUTE format('ALTER INDEX %I RENAME TO %I', r.relname, r.relname || '_before_v205');
    END LOOP;

    CREATE TABLE stats_events (
        created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
        updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
        id VARCHAR(100) NOT NULL,
        source_id VARCHAR(100),
        index VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        source JSONB,
        date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
        CONSTRAINT pk_stats_events PRIMARY KEY (id, date),
        CONSTRAINT uq_stats_key_stats_events UNIQUE (source_id, index, date)
    ) PARTITION BY RANGE (date);
    CREATE INDEX ix_stats_events_date ON stats_events (date);

    SELECT make_date(LEAST(COALESCE(extract(year FROM min(date))::int,
                                    extract(year FROM now())::int),
                           extract(year FROM now())::int), 1, 1)
      INTO first_month FROM stats_events_before_v205;
    last_month := make_date(extract(year FROM now())::int + 1, 12, 1);

    m := first_month;
    WHILE m <= last_month LOOP
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF stats_events FOR VALUES FROM (%L) TO (%L)',
            'stats_events_' || to_char(m, 'YYYYMM'), m, (m + interval '1 month')::date);
        m := (m + interval '1 month')::date;
    END LOOP;

    INSERT INTO stats_events (created, updated, id, source_id, index, type, source, date)
    SELECT created, updated, id, source_id, index, type, source, date
      FROM stats_events_before_v205;
    GET DIAGNOSTICS moved = ROW_COUNT;
    SELECT count(*) INTO old_rows FROM stats_events_before_v205;
    IF moved <> old_rows THEN
        RAISE EXCEPTION 'stats_events: copied % of % rows', moved, old_rows;
    END IF;

    DROP TABLE stats_events_before_v205;
    RAISE NOTICE 'stats_events: % rows moved into partitions from % to %', moved, first_month, last_month;
END$$;

-- The primary key is looked up by table, as its name may differ on sites
-- whose tables were not created by SQLAlchemy.
DO $$
DECLARE
    t TEXT;
    pk_name TEXT;
    pk_cols TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['stats_aggregation', 'stats_bookmark'] LOOP
        SELECT c.conname, string_agg(a.attname, ',' ORDER BY a.attname)
          INTO pk_name, pk_cols
          FROM pg_constraint c
          JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
         WHERE c.conrelid = t::regclass AND c.contype = 'p'
         GROUP BY c.conname;
        IF pk_cols IS DISTINCT FROM 'date,id' THEN
            IF pk_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', t, pk_name);
            END IF;
            EXECUTE format('ALTER TABLE %I ADD CONSTRAINT %I PRIMARY KEY (id, date)',
                           t, 'pk_' || t);
            RAISE NOTICE '%: primary key changed from (%) to (id, date)', t, pk_cols;
        END IF;
    END LOOP;
END$$;

COMMIT;
