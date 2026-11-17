-- MAR corpora administration V1: ADDITIVE schema only. No media, Neon Auth or P0 tables.
-- Run on an ISOLATED Neon branch first with a direct connection.
-- Do not merge to production without PR review, P0 recovery gate and a verified rollback.

CREATE SCHEMA IF NOT EXISTS mar_corpora;

CREATE TABLE IF NOT EXISTS mar_corpora.connector_registry (
    corpus_code text PRIMARY KEY
        CHECK (corpus_code ~ '^[a-z][a-z0-9-]{1,63}$'),
    institution text NOT NULL CHECK (length(btrim(institution)) BETWEEN 1 AND 300),
    adapter_module text NOT NULL
        CHECK (adapter_module ~ '^memoria_audiovisual\.[a-z][a-z0-9_]*$'),
    record_hosts text[] NOT NULL
        CHECK (cardinality(record_hosts) BETWEEN 1 AND 20),
    source_kind text NOT NULL
        CHECK (source_kind IN ('institutional_record', 'aggregated_institutional_record')),
    spec_sha256 text NOT NULL CHECK (spec_sha256 ~ '^[0-9a-f]{64}$'),
    registered_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mar_corpora.audit_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    corpus_code text NOT NULL REFERENCES mar_corpora.connector_registry(corpus_code),
    event_kind text NOT NULL CHECK (event_kind IN (
        'registered', 'probed', 'evidence_validated', 'curator_reviewed',
        'admission_ready', 'HOLD', 'note'
    )),
    actor_ref text NOT NULL CHECK (length(btrim(actor_ref)) BETWEEN 4 AND 160),
    evidence_sha256 text CHECK (evidence_sha256 IS NULL OR evidence_sha256 ~ '^[0-9a-f]{64}$'),
    evidence_ref text CHECK (evidence_ref IS NULL OR length(evidence_ref) <= 500),
    note text NOT NULL DEFAULT '' CHECK (length(note) <= 600),
    recorded_at timestamptz NOT NULL DEFAULT now(),
    CHECK (event_kind IN ('HOLD', 'note') OR evidence_sha256 IS NOT NULL)
);

CREATE UNIQUE INDEX IF NOT EXISTS mar_corpora_one_registration
    ON mar_corpora.audit_events (corpus_code) WHERE event_kind = 'registered';

CREATE UNIQUE INDEX IF NOT EXISTS mar_corpora_one_probe_per_evidence
    ON mar_corpora.audit_events (corpus_code, event_kind, evidence_sha256)
    WHERE event_kind = 'probed';

CREATE INDEX IF NOT EXISTS mar_corpora_audit_recent_by_corpus
    ON mar_corpora.audit_events (corpus_code, event_id DESC);

CREATE INDEX IF NOT EXISTS mar_corpora_audit_recent_global
    ON mar_corpora.audit_events (event_id DESC);

CREATE OR REPLACE VIEW mar_corpora.current_status AS
SELECT c.corpus_code, c.institution, c.adapter_module,
       c.record_hosts, c.source_kind, c.spec_sha256, c.registered_at,
       e.event_id AS last_event_id, e.event_kind AS last_reported_stage,
       e.actor_ref AS last_actor_ref, e.evidence_sha256 AS last_evidence_sha256,
       e.recorded_at AS last_event_at,
       false AS publication_authorized,
       false AS scientific_validation_proven_by_database
FROM mar_corpora.connector_registry AS c
LEFT JOIN LATERAL (
    SELECT event_id, event_kind, actor_ref, evidence_sha256, recorded_at
    FROM mar_corpora.audit_events
    WHERE corpus_code = c.corpus_code AND event_kind <> 'note'
    ORDER BY event_id DESC LIMIT 1
) AS e ON true;

-- Append-only even if a mistakenly overprivileged application role attempts
-- to mutate rows. Database owner can change triggers: this is NOT WORM.
CREATE OR REPLACE FUNCTION mar_corpora.reject_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'MAR corpus audit/registry records are append-only';
END;
$$;

CREATE TRIGGER mar_corpora_registry_immutable
BEFORE UPDATE OR DELETE OR TRUNCATE ON mar_corpora.connector_registry
FOR EACH STATEMENT EXECUTE FUNCTION mar_corpora.reject_mutation();

CREATE TRIGGER mar_corpora_audit_immutable
BEFORE UPDATE OR DELETE OR TRUNCATE ON mar_corpora.audit_events
FOR EACH STATEMENT EXECUTE FUNCTION mar_corpora.reject_mutation();

-- Group privileges only. Do not grant these roles to production principals
-- until separate, individually scoped credentials and approvals exist.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mar_corpora_reader') THEN
        CREATE ROLE mar_corpora_reader NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'mar_corpora_ingester') THEN
        CREATE ROLE mar_corpora_ingester NOLOGIN;
    END IF;
END;
$$;

REVOKE ALL ON SCHEMA mar_corpora FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA mar_corpora FROM PUBLIC;
GRANT USAGE ON SCHEMA mar_corpora TO mar_corpora_reader, mar_corpora_ingester;
GRANT SELECT ON mar_corpora.connector_registry,
    mar_corpora.audit_events, mar_corpora.current_status TO mar_corpora_reader;
GRANT SELECT ON mar_corpora.connector_registry,
    mar_corpora.audit_events, mar_corpora.current_status TO mar_corpora_ingester;
GRANT INSERT ON mar_corpora.connector_registry,
    mar_corpora.audit_events TO mar_corpora_ingester;
GRANT USAGE, SELECT ON SEQUENCE mar_corpora.audit_events_event_id_seq
    TO mar_corpora_ingester;
