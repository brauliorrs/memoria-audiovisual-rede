"""Explicitly opted-in live Psycopg integration, confined to MAR's Neon test branch.

Never enabled by the ordinary CI. Synthetic records only; no external collection.
Use MAR_P0_TEST_LIVE=1 + MAR_P0_TEST_DATABASE_URL on a trusted runner.
"""
from __future__ import annotations

import os
import tempfile
import unittest
import uuid
from pathlib import Path

from memoria_audiovisual.metadata_staging import MetadataPage, StageRejected, stage_metadata
from memoria_audiovisual.postgres_checkpoint_storage import (
    PersistenceRejected,
    PostgresCheckpointStore,
)

# Verified with Neon's branch-compute API. Changing Neon endpoint requires review.
TEST_ENDPOINT = "ep-damp-term-b8wqhmz0.c-14.us-east-1.aws.neon.tech"
TEST_BRANCH = "br-lingering-smoke-b8hjdnzb"


class SyntheticSource:
    """Two metadata-only pages; no HTTP, no provider API or media bytes."""

    scope = {"institution": "fiaf-kavi", "evidence": "a" * 64}

    def preflight(self) -> int:
        return 2

    def fetch_page(self, token: str | None) -> MetadataPage:
        if token is None:
            identifier, next_token = "p0-test-001", "synthetic-opaque-cursor"
        elif token == "synthetic-opaque-cursor":
            identifier, next_token = "p0-test-002", None
        else:
            raise StageRejected("synthetic_cursor_unknown")
        record = {"id": identifier, "title": "Synthetic record", "media_downloaded": False}
        return MetadataPage(
            (record,), 2, next_token,
            {"status": "OK", "resultCount": 2, "records": [record]},
        )


@unittest.skipUnless(
    os.environ.get("MAR_P0_TEST_LIVE") == "1",
    "Live Neon adapter test requires explicit opt-in on a trusted runner",
)
class NeonLiveIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import psycopg
        from psycopg.conninfo import conninfo_to_dict

        dsn = os.environ.get("MAR_P0_TEST_DATABASE_URL", "")
        if not dsn:
            raise RuntimeError("MAR_P0_TEST_DATABASE_URL_required")
        settings = conninfo_to_dict(dsn)
        # Hard stop before opening even one connection to a mistaken database.
        if (
            settings.get("host") != TEST_ENDPOINT
            or settings.get("hostaddr")
            or settings.get("service")
            or settings.get("dbname") != "neondb"
            or settings.get("sslmode") not in {"require", "verify-ca", "verify-full"}
        ):
            raise RuntimeError("p0_isolated_branch_connection_guard_failed")
        cls.psycopg = psycopg
        cls.dsn = dsn
        cls.store = PostgresCheckpointStore(lambda: psycopg.connect(dsn))

    def test_save_recover_resume_and_sql_integrity(self) -> None:
        key = "p0-psycopg-live-" + uuid.uuid4().hex
        source = SyntheticSource()
        with tempfile.TemporaryDirectory(prefix="mar-p0-live-") as folder:
            root = Path(folder)
            staged, recovered, complete = (
                root / "staged", root / "recovered", root / "complete"
            )
            initial = stage_metadata(source, staged, max_pages=1)
            self.assertEqual(initial["status"], "partial")

            self.assertEqual(self.store.save(staged, key), 1)
            self.assertEqual(self.store.save(staged, key), 1)
            self.assertEqual(
                self.store.restore(
                    recovered, key,
                    expected_scope=source.scope, expected_total=2,
                ), 1,
            )
            self.assertEqual(
                (staged / "checkpoint.json").read_bytes(),
                (recovered / "checkpoint.json").read_bytes(),
            )
            self.assertEqual(
                stage_metadata(source, recovered, max_pages=1, resume=True)["status"],
                "complete",
            )
            self.assertEqual(
                self.store.save(recovered, key, expected_revision=1), 2
            )
            self.assertEqual(
                self.store.restore(
                    complete, key, expected_scope=source.scope, expected_total=2
                ), 2
            )
            self.assertEqual(
                (recovered / "checkpoint.json").read_bytes(),
                (complete / "checkpoint.json").read_bytes(),
            )
            self.assertEqual(stage_metadata(source, complete, resume=True)["status"],
                             "complete")

            with self.psycopg.connect(self.dsn) as conn:
                row = conn.execute(
                    "SELECT revision,status,record_count,"
                    " encode(sha256(manifest),'hex')=manifest_sha256,"
                    " (SELECT count(*) FROM mar_p0.checkpoint_pages WHERE run_key=%s)"
                    " FROM mar_p0.checkpoints WHERE run_key=%s",
                    (key, key),
                ).fetchone()
            self.assertEqual(row, (2, "complete", 2, True, 2))

            with self.assertRaisesRegex(PersistenceRejected, "write_conflict"):
                self.store.save(staged, key, expected_revision=1)
            with self.assertRaisesRegex(PersistenceRejected, "destination_exists"):
                self.store.restore(
                    complete, key, expected_scope=source.scope, expected_total=2
                )

    def test_transaction_rollback_on_invalid_sha(self) -> None:
        """Driver ↔ Neon transaction rollback, with no persistent test row."""
        key = "p0-psycopg-rollback-" + uuid.uuid4().hex
        with self.assertRaises(self.psycopg.errors.CheckViolation):
            with self.psycopg.connect(self.dsn) as conn:
                raw = b'{"synthetic":true}\n'
                conn.execute(
                    "INSERT INTO mar_p0.checkpoints "
                    "(run_key, scope_sha256, revision, manifest, manifest_sha256,"
                    " status, expected_total, record_count) "
                    "VALUES (%s,%s,1,%s,encode(sha256(%s),'hex'),'partial',1,0)",
                    (key, "a" * 64, raw, raw),
                )
                conn.execute(
                    "INSERT INTO mar_p0.raw_artifacts (sha256,payload)"
                    " VALUES (%s,%s)",
                    ("f" * 64, b"tampered"),
                )
        with self.psycopg.connect(self.dsn) as conn:
            remaining = conn.execute(
                "SELECT count(*) FROM mar_p0.checkpoints WHERE run_key=%s",
                (key,),
            ).fetchone()[0]
        self.assertEqual(remaining, 0)


if __name__ == "__main__":
    unittest.main()
