-- MAR Gate P0: isolated, additive pilot schema (PostgreSQL 18).
-- IMPORTANT: Never run this on the MAR published corpus or on another project's DB.
-- Apply ONCE on a dedicated Neon testing branch. No automatic collection or promotion.
-- The schema intentionally stores original bytes; JSONB reserialization is not used.

CREATE SCHEMA mar_p0;

CREATE TABLE mar_p0.raw_artifacts (
    sha256 text PRIMARY KEY CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    payload bytea NOT NULL,
    byte_size integer GENERATED ALWAYS AS (octet_length(payload)) STORED,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT artifact_hash_matches
        CHECK (sha256 = encode(pg_catalog.sha256(payload), 'hex'))
);

CREATE TABLE mar_p0.checkpoints (
    run_key text PRIMARY KEY CHECK (length(run_key) BETWEEN 1 AND 200),
    scope_sha256 text NOT NULL CHECK (scope_sha256 ~ '^[0-9a-f]{64}$'),
    revision integer NOT NULL CHECK (revision >= 1),
    manifest bytea NOT NULL,
    manifest_sha256 text NOT NULL
        CHECK (manifest_sha256 ~ '^[0-9a-f]{64}$'),
    status text NOT NULL CHECK (status IN ('partial', 'complete')),
    expected_total integer NOT NULL CHECK (expected_total >= 0),
    record_count integer NOT NULL
        CHECK (record_count BETWEEN 0 AND expected_total),
    promotion_authorized boolean NOT NULL DEFAULT false
        CHECK (NOT promotion_authorized),
    media_downloaded boolean NOT NULL DEFAULT false
        CHECK (NOT media_downloaded),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT checkpoint_hash_matches
        CHECK (manifest_sha256 = encode(pg_catalog.sha256(manifest), 'hex'))
);

CREATE TABLE mar_p0.checkpoint_pages (
    run_key text NOT NULL REFERENCES mar_p0.checkpoints(run_key),
    sequence integer NOT NULL CHECK (sequence > 0),
    artifact_sha256 text NOT NULL REFERENCES mar_p0.raw_artifacts(sha256),
    record_count integer NOT NULL CHECK (record_count >= 0),
    ids_sha256 text NOT NULL CHECK (ids_sha256 ~ '^[0-9a-f]{64}$'),
    input_cursor_sha256 text NOT NULL
        CHECK (input_cursor_sha256 ~ '^[0-9a-f]{64}$'),
    next_cursor_sha256 text
        CHECK (next_cursor_sha256 IS NULL
               OR next_cursor_sha256 ~ '^[0-9a-f]{64}$'),
    PRIMARY KEY (run_key, sequence),
    UNIQUE (run_key, artifact_sha256)
);

-- Contract for the future Python adapter (not enabled here):
-- 1. Before writing, re-run metadata_staging._restore against every original artifact.
-- 2. In ONE SQL transaction, insert immutable artifacts, CAS-update the checkpoint
--    WHERE run_key = :run_key AND revision = :expected_revision, then add pages.
-- 3. Reject zero-row CAS updates, non-append-only pages, mismatched scope/total,
--    missing artifacts, stale cursors and duplicate record IDs (fail closed).
-- 4. After read, verify checksums and replay metadata_staging._restore again.
-- 5. Keep resumption tokens and raw provider data confidential; never print to CI.
-- 6. No INSERTs into scientific corpus tables and no ingestion from remote sources.
