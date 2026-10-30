-- Records which upgrade steps have been applied, so that steps that must run
-- only once (update_v0927, W2025-29.sql, ...) are skipped on a rerun.
CREATE TABLE IF NOT EXISTS weko_upgrade_v205_steps (
    step VARCHAR(100) NOT NULL,
    done_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    CONSTRAINT pk_weko_upgrade_v205_steps PRIMARY KEY (step)
);
