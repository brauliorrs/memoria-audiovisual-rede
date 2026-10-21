-- Synthetic-only, rollback-only Neon Gate P0 SQL smoke test.
-- Prerequisites: apply sql/migrations/001_mar_p0_checkpoint.sql on a TEST branch.
-- Set psql -v ON_ERROR_STOP=1; never point at main or a scientific corpus.
BEGIN;

INSERT INTO mar_p0.raw_artifacts(sha256, payload)
SELECT encode(sha256(convert_to('{"synthetic":true}', 'UTF8')), 'hex'),
       convert_to('{"synthetic":true}', 'UTF8');

INSERT INTO mar_p0.checkpoints (
  run_key, scope_sha256, revision, manifest, manifest_sha256,
  status, expected_total, record_count
)
SELECT 'p0-smoke-rollback', repeat('a', 64), 1,
       convert_to('{"synthetic":true,"media_downloaded":false,"promotion_authorized":false}', 'UTF8'),
       encode(sha256(convert_to('{"synthetic":true,"media_downloaded":false,"promotion_authorized":false}', 'UTF8')), 'hex'),
       'partial', 1, 1;

INSERT INTO mar_p0.checkpoint_pages (
  run_key, sequence, artifact_sha256, record_count,
  ids_sha256, input_cursor_sha256, next_cursor_sha256
)
SELECT 'p0-smoke-rollback', 1, sha256, 1, repeat('b', 64),
       repeat('c', 64), repeat('d', 64)
FROM mar_p0.raw_artifacts
WHERE payload = convert_to('{"synthetic":true}', 'UTF8');

DO $tests$
DECLARE
  blocked boolean := false;
BEGIN
  BEGIN
    INSERT INTO mar_p0.raw_artifacts(sha256, payload)
    VALUES (repeat('f', 64), convert_to('tampered', 'UTF8'));
  EXCEPTION WHEN check_violation THEN
    blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'FAIL: corrupt artifact accepted'; END IF;

  blocked := false;
  BEGIN
    INSERT INTO mar_p0.checkpoint_pages (
      run_key, sequence, artifact_sha256, record_count,
      ids_sha256, input_cursor_sha256, next_cursor_sha256
    )
    SELECT 'p0-smoke-rollback', 1, sha256, 1, repeat('b', 64),
           repeat('c', 64), repeat('d', 64)
    FROM mar_p0.raw_artifacts
    WHERE payload = convert_to('{"synthetic":true}', 'UTF8');
  EXCEPTION WHEN unique_violation THEN
    blocked := true;
  END;
  IF NOT blocked THEN RAISE EXCEPTION 'FAIL: duplicate page accepted'; END IF;

  UPDATE mar_p0.checkpoints SET revision = revision + 1
  WHERE run_key = 'p0-smoke-rollback' AND revision = 0;
  IF FOUND THEN RAISE EXCEPTION 'FAIL: stale writer advanced revision'; END IF;

  IF NOT EXISTS (
    SELECT 1 FROM mar_p0.checkpoints
    WHERE run_key = 'p0-smoke-rollback'
      AND revision = 1 AND status = 'partial'
      AND manifest_sha256 = encode(sha256(manifest), 'hex')
  ) THEN RAISE EXCEPTION 'FAIL: checkpoint changed unexpectedly'; END IF;
  RAISE NOTICE 'PASS: artifact tamper, duplicate page, stale CAS and checkpoint integrity';
END;
$tests$;

-- The fixture never persists, even if the user runs this script repeatedly.
ROLLBACK;
