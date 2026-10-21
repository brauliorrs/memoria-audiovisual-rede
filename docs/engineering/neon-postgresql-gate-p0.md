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

**Impact of this PR:** adds only the pilot SQL schema, a rollback-only SQL smoke test, and documentation. No application imports, dependencies, schedulers, collectors, public corpus, production branch or published results change.

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

A future adapter must preserve **append-only page history** and use one SQL transaction to atomically persist artifact bytes + compare-and-swap checkpoint revision + page references. Data retrieved from the database must be replayed through the current stage validation algorithm (including record ID and cursor chain checks); database constraints alone do not implement all of those validations.

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

1. Implement a standalone Python storage adapter (no change to the Finna source adapter), with an explicit API for save/load and optimistic revision checking. Add deterministic unit and integration tests preserving the existing `_restore` validation contract.
2. Define a dedicated least-privilege SQL role and secret handling outside source control. Use SSL/TLS, preferably with pooling suitable for short-lived Python workers. Never log credentials or provider cursor contents.
3. Produce an encrypted independent backup of artifact bytes and checkpoint metadata, including hashes, and **restore it into a fresh independent target**. Document tested RPO/RTO and retention.
4. Test missing/tampered artifacts, scope drift, duplicate IDs between pages, cursor cycles, crash before/after transaction commit, concurrent writers and refusal to promote.
5. Measure actual corpus payload sizes, index overhead, expected daily writes, queries and Neon CU-hours; validate practical headroom against the **observed 512 MiB**, not an advertised ceiling.
6. Run CI and obtain human review. Only after all checks pass can the schema be proposed for controlled production activation; no mass ingestion is authorized by this pilot.

## Reproducibility

The migration file contains the exact DDL used in the isolated branch. `tests/integration/p0_neon_contract.sql` is a disposable **ROLLBACK-only** smoke test; it requires a test branch and `psql -v ON_ERROR_STOP=1`. It tests SQL constraints, not the Python source adapter or production recovery.

**Decision: P0 remains HOLD for production.** The Neon resource itself is available and the basic database storage experiment succeeded, but protected durable persistence, verified backup and real collector integration are not yet approved.
