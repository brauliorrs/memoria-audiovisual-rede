# Gate P0 — Neon PostgreSQL: pilot schema and controlled validation

**Date:** 2026-10-21. **Status:** isolated proof of concept **PASS for basic SQL integrity and branch-copy recovery**; **P0 for production NOT APPROVED**.

## Scope and impact audit (before changing collectors)

The source of truth for current metadata staging is `src/memoria_audiovisual/metadata_staging.py`; its baseline is `tests/test_metadata_staging.py`, with Finna semantics covered by `src/memoria_audiovisual/kavi_finna_adapter.py` and `tests/test_kavi_finna_adapter.py`.

Existing contracts must remain unchanged:
- `STAGING_SCHEMA = "1.0.0"`, source `scope_sha256` and preflight count bind resume to the approved source.
- Immutable JSON bytes from `digital_infrastructure.raw_artifacts.canonical_json_bytes` are identified by SHA-256; the checkpoint's on-disk JSON includes one trailing LF. **PostgreSQL JSONB must not substitute for the preserved original bytes.**
- `_restore` replays every artifact, validates hashes, page order, cursor hash chain, cross-page record-ID uniqueness, count, and rejects tampering.
- `promotion_authorized` and `media_downloaded` remain `false`.
- Finna continuation tokens can be sensitive; only hashes belong in published checkpoint summaries. Raw staged pages are access-restricted.
- `scripts/run_observatory_cycle.py`, public `data/output`, `app/streamlit_app.py`, and all scientific instrument registries are **out of scope**.

**Impact of this PR:** adds the pilot SQL schema, an opt-in Python storage adapter, deterministic tests, an optional driver dependency, and documentation. No collection scheduler, existing collector, public corpus, default Neon branch, Streamlit view or scientific instrument is modified.

## Actual infrastructure observed

- Provider resource: `neon-erin-field`, managed by Vercel; separate from the unrelated `submeta-ai-db`.
- Project identifier: `holy-bread-70461948`; PostgreSQL **18.6**, region `aws-us-east-1`.
- Production/default branch `main` (`br-raspy-river-b8qx9oo9`) was **not changed**.
- Test branch `mar-p0-validation-20261021` (`br-lingering-smoke-b8hjdnzb`).
- Recovery-copy branch `mar-p0-recovery-20261021` (`br-holy-dawn-b8z9t6yh`).
- Actual project API currently shows a **512 MiB branch logical size limit**, notwithstanding a newer marketing announcement of 1 GB for Free. Capacity approval must use the enforced project limit until it is verified otherwise.
- Restorable-history setting observed: **6 hours**. This does **not** satisfy independent backup retention.

## Relational pilot design

Apply `sql/migrations/001_mar_p0_checkpoint.sql` **once** on a disposable validation branch, not on `main`.

| Relation | Purpose | Key invariant |
|---|---|---|
| `mar_p0.raw_artifacts` | Original content-addressed JSON bytes | SQL check recomputes SHA-256 over `bytea` |
| `mar_p0.checkpoints` | Serialized checkpoint, scope, CAS revision, status | SHA-256 validation; no promotion/media flags |
| `mar_p0.checkpoint_pages` | Ordered page-to-artifact references and cursor/ID hashes | Foreign keys, unique sequence and artifact per run |

The opt-in Python adapter must preserve **append-only page history** and use one SQL transaction to atomically persist artifact bytes + compare-and-swap checkpoint revision + page references. Data retrieved from the database must be replayed through the current stage validation algorithm (including record ID and cursor chain checks); database constraints alone do not implement all of those validations.

No media, thumbnails, audiovisual binaries, public viewer or derived research metric belong in this pilot.

## Live synthetic results (2026-10-21)

Only two synthetic metadata records, `synthetic-001` and `synthetic-002`, were used. No request was made to Finna or any other source.

| Test | Observed result |
|---|---|
| Insert content-addressed artifact + partial checkpoint | PASS, both SHA-256 checks true |
| Insert corrupted bytes with an asserted hash | PASS, DB rejected `artifact_hash_matches` |
| Insert duplicate sequence of a checkpoint page | PASS, DB rejected `checkpoint_pages_pkey` |
| Simulate stale compare-and-swap revision | PASS, updated zero rows |
| Transition 1 page / 1 record into 2 pages / 2 records | PASS, revision advanced 1 → 2, complete |
| Validate both artifact hashes and manifest hash | PASS |
| Clone testing branch and read back original manifest/checkpoint | PASS, manifest SHA-256 identical |
| Snapshot through Neon snapshot API | NOT AVAILABLE: non-root branches cannot be snapshotted with this integration |
| Independent off-provider export, backup retention, disaster recovery | NOT TESTED; mandatory P0 blocker |
| Restricted database role, authentication rotation and application adapter | NOT IMPLEMENTED; mandatory P0 blocker |
| Simultaneous writers, disconnect during commit, source-level full replay | NOT TESTED; mandatory P0 blocker |

Recovered synthetic manifest SHA-256: `c78a286ad7f92fb9baacfe66904c3147742a99e4ba160209213859909d6b1aa2`. The two test branches have identical record count, page count, revision and manifest checksum.

The clone proves branch-level recovery in the same provider. **It is not an independent backup or a tested restore following provider loss.**

## Release gates still required

1. **IMPLEMENTED FOR TEST:** standalone `PostgresCheckpointStore` with transactional `save`, scoped `restore`, strict CAS revisions, immutability, byte-perfect checks and replay through `_restore`. Offline tests are in `tests/test_postgres_checkpoint_storage.py`. The adapter is not wired into the collector or default scheduler. **LIVE end-to-end Python↔Neon integration and full CI verdict remain pending.**
2. Define a dedicated least-privilege SQL role and secret handling outside source control. Use SSL/TLS, preferably with pooling suitable for short-lived Python workers. Never log credentials or provider cursor contents.
3. Produce an encrypted independent backup of artifact bytes and checkpoint metadata, including hashes, and **restore it into a fresh independent target**. Document tested RPO/RTO and retention.
4. Test missing/tampered artifacts, scope drift, duplicate IDs between pages, cursor cycles, crash before/after transaction commit, concurrent writers and refusal to promote.
5. Measure actual corpus payload sizes, index overhead, expected daily writes, queries and Neon CU-hours; validate practical headroom against the **observed 512 MiB**, not an advertised ceiling.
6. Run CI and obtain human review. Only after all checks pass can the schema be proposed for controlled production activation; no mass ingestion is authorized by this pilot.

## Reproducibility

The migration file contains the exact DDL used in the isolated branch. `tests/integration/p0_neon_contract.sql` is a disposable **ROLLBACK-only** smoke test; it requires a test branch and `psql -v ON_ERROR_STOP=1`. It tests SQL constraints, not the Python source adapter or production recovery.

**Decision: P0 remains HOLD for production.** The Neon resource itself is available and the basic database storage experiment succeeded, but protected durable persistence, verified backup and real collector integration are not yet approved.

## Python adapter added in the isolated PR

Install the optional PostgreSQL driver **only on an authorized test executor**:

```bash
python -m pip install -e '.[postgres]'
```

Usage from controlled Python code with an explicit connection factory (do not embed any secret in source, CI output or logs):

```python
import os
import psycopg
from memoria_audiovisual.postgres_checkpoint_storage import PostgresCheckpointStore

dsn = os.environ["MAR_P0_TEST_DATABASE_URL"]  # restricted isolated Neon branch
store = PostgresCheckpointStore(lambda: psycopg.connect(dsn))

# After an existing, bounded offline stage has produced a complete or partial
# verified checkpoint directory. No fetch happens inside the storage adapter:
revision = store.save("/protected/staging/kavi-test", "kavi-offline-p0")

# Recovery always requires the original approved scope and preflight total.
# Destination must NOT exist: prevents silent overwrite of ongoing local work.
store.restore(
    "/protected/staging/kavi-recovered", "kavi-offline-p0",
    expected_scope=approved_scope, expected_total=approved_total,
)
```

The connection factory is injected to allow deterministic offline tests. Production credentials are **not** automatically loaded from a default `DATABASE_URL`, since that could belong to a different application. The application must use a dedicated least-privilege role, TLS-enforced external connection configuration, and an explicit test-branch binding before enabling writes.

**Persistence semantics:** `save` reads the canonical existing `checkpoint.json` and every content-addressed JSON artefact, replays the existing MAR contract, and stores them in one database transaction. The caller must pass `expected_revision` for every update; stale writers are rejected. Identical retries are idempotent. `restore` loads and verifies all original bytes, hashes, scope, expected count, page/cursor chain and record-ID uniqueness, and moves a complete temporary directory into place without modifying an existing target. All database writes use bound query parameters.

**Boundaries:** these operations do not call `stage_metadata`, start any network collection, promote records, alter the Streamlit app or schedule background work. The unchanged original `stage_metadata(..., resume=True)` must still run its preflight and verification upon continuation.

Run deterministic checks with:

```bash
python -m unittest discover -s tests -p 'test_postgres_checkpoint_storage.py' -v
python -m unittest discover -s tests -p 'test_metadata_staging.py' -v
ruff check --select E9,F63,F7,F82 src/memoria_audiovisual/postgres_checkpoint_storage.py tests/test_postgres_checkpoint_storage.py
```

**Remaining P0 blockers:** independent encrypted off-provider backup and fresh-database restore; dedicated restricted database role and credential rotation; tests with a real Psycopg connection and two simultaneous writers, explicit fail-before/fail-after commit, and actual quota measurement. Branch cloning is not equivalent to an independent backup. Production remains HOLD.

## Live database contract checks on isolated Neon branch (2026-10-21)

**Proven execution through Neon SQL connections** (not Python/Psycopg):
- Data remained only on `mar-p0-validation-20261021`. Production `main` has no `mar_p0` schema.
- Transaction with a synthetically inserted checkpoint followed by an invalid SHA-256 artifact **failed**, and an independent read confirmed **zero orphan rows** for the failed checkpoint.
- Two competing compare-and-swap updates against the same synthetic revision were submitted concurrently: **one** returned revision 2, **one** returned zero updated rows, and the database finished at revision 2 with both pages intact.
- Creating a role through the Neon API yielded overly broad built-in `neon_superuser` membership, `CREATEDB` and `CREATEROLE`. The attempted privilege reduction was denied. The newly created unsafe test role was **deleted**. Do not use Neon API-created default-privileged roles for MAR application credentials.
- A separate **NOLOGIN** role was created explicitly by SQL: `mar_p0_limited NOLOGIN NOCREATEDB NOCREATEROLE NOINHERIT`. Explicit grants enable MAR's three pilot tables. Under `SET LOCAL ROLE mar_p0_limited`, a synthetic checkpoint and page references were inserted successfully; attempts to query `neon_auth.user` failed with a permission-denied error. The role cannot create database objects or objects in `public`. This verifies least-privilege SQL grants only; an authenticated external LOGIN role is not yet configured.
- Raw content remained metadata-only; no source API was called.

**Psycopg driver ↔ Neon execution: STILL NOT VERIFIED.** The connector's SQL operations cannot establish that the Python driver successfully connected, executed its transaction context manager, or recovered a local staging directory across a process boundary. Never upgrade these SQL-only results to a successful Python integration claim.

### Guarded Python integration harness

`tests/test_neon_checkpoint_live.py` is a concrete opt-in integration test. It uses only synthetic `MetadataPage` fixtures, exercises `PostgresCheckpointStore.save/restore`, resumes the original `stage_metadata` contract, verifies exact checkpoint bytes, SQL hashes and counts, CAS conflicts and a failing driver transaction that must roll back.

It is skipped in ordinary CI and requires **both** an explicit opt-in and a private connection string whose host is the exact test branch compute endpoint. This prevents accidental connection to the Neon default/production branch.

On an individually controlled trusted runner, after creating an SQL-native, **least-privileged LOGIN role** and loading the password from a secure store (do not use the Neon default owner), run:

```bash
python -m pip install -e '.[postgres]'
export MAR_P0_TEST_LIVE=1
# MAR_P0_TEST_DATABASE_URL must be sourced from a secret manager, not committed.
# Required host: ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech
# Required database: neondb; sslmode=require or stricter.
python -m unittest discover -s tests -p 'test_neon_checkpoint_live.py' -v
```

**Never** put a Neon DSN into a GitHub issue, pull-request description, source file or untrusted PR CI job. Do not enable live tests simply by adding a broad repository secret to a public pull-request workflow. Verify the role and branch allowlist first, and use a manually controlled test executor with isolated credentials.

**Remaining blockers:** genuine Psycopg↔Neon integration verdict, SQL-native least-privileged LOGIN credentials and secure secret injection, encrypted **off-provider** backups with a tested restore into a fresh independent database, resilience against worker crash and credential rotation. P0 remains HOLD for operational use.
