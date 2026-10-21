"""Deterministic storage adapter tests: no Neon credentials or remote collection."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.metadata_staging import MetadataPage, StageRejected, stage_metadata
from memoria_audiovisual.postgres_checkpoint_storage import (
    PersistenceRejected, PostgresCheckpointStore,
)


class _Result:
    def __init__(self, rows=(), rowcount=0):
        self.rows = list(rows)
        self.rowcount = rowcount

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class _Database:
    """Transaction-aware fake of the fixed SQL surface used by the adapter."""

    def __init__(self):
        self.artifacts = {}
        self.checkpoints = {}
        self.pages = {}
        self.fail_at = None

    def connect(self):
        return _Connection(self)


class _Connection:
    def __init__(self, db):
        self.db = db

    def __enter__(self):
        self.original = copy.deepcopy((
            self.db.artifacts, self.db.checkpoints, self.db.pages,
        ))
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            (self.db.artifacts, self.db.checkpoints, self.db.pages) = self.original
        return False

    def execute(self, sql, args):
        db = self.db
        if db.fail_at and db.fail_at in sql:
            raise RuntimeError("synthetic_database_disconnection")
        if sql.startswith("SELECT revision"):
            row = db.checkpoints.get(args[0])
            return _Result([row] if row is not None else [])
        if sql.startswith("SELECT p.sequence"):
            rows = [
                (*page, db.artifacts.get(page[1]))
                for page in db.pages.get(args[0], [])
            ]
            return _Result(sorted(rows, key=lambda p: p[0]))
        if sql.startswith("INSERT INTO mar_p0.raw_artifacts"):
            key, data = args
            if key not in db.artifacts:
                db.artifacts[key] = data
            return _Result(rowcount=1)
        if sql.startswith("INSERT INTO mar_p0.checkpoints"):
            run_key, scope, revision, data, digest, status, total, count = args
            if run_key in db.checkpoints:
                raise RuntimeError("duplicate_key")
            db.checkpoints[run_key] = (
                revision, scope, total, data, digest, status, count,
            )
            return _Result(rowcount=1)
        if sql.startswith("UPDATE mar_p0.checkpoints"):
            revision, data, digest, status, count, run_key, expected = args
            old = db.checkpoints[run_key]
            if old[0] != expected:
                return _Result(rowcount=0)
            db.checkpoints[run_key] = (
                revision, old[1], old[2], data, digest, status, count,
            )
            return _Result(rowcount=1)
        if sql.startswith("INSERT INTO mar_p0.checkpoint_pages"):
            run_key, *values = args
            db.pages.setdefault(run_key, [])
            if any(old[0] == values[0] for old in db.pages[run_key]):
                raise RuntimeError("duplicate_key")
            db.pages[run_key].append(tuple(values))
            return _Result(rowcount=1)
        raise AssertionError("unknown SQL operation")


class _Source:
    def __init__(self):
        self.scope = {
            "institution": "fiaf-kavi",
            "evidence": "a" * 64,
        }
        self.requested = []

    def preflight(self):
        return 2

    def fetch_page(self, token):
        self.requested.append(token)
        if token is None:
            ids, next_token = ["synthetic-001"], "private-synthetic-cursor"
        elif token == "private-synthetic-cursor":
            ids, next_token = ["synthetic-002"], None
        else:
            raise AssertionError("unexpected token")
        records = tuple(
            {"id": i, "title": "Synthetic", "media_downloaded": False}
            for i in ids
        )
        return MetadataPage(
            records, 2, next_token,
            {"status": "OK", "records": list(records), "resultCount": 2},
        )


class PostgresCheckpointStorageTests(unittest.TestCase):
    def setUp(self):
        self.db = _Database()
        self.store = PostgresCheckpointStore(self.db.connect)

    @staticmethod
    def _partial(root):
        source = _Source()
        payload = stage_metadata(source, root, max_pages=1)
        assert payload["status"] == "partial"
        return source

    def test_partial_save_restore_and_original_runner_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            staged, restored, finished = root / "staged", root / "recovered", root / "finished"
            source = self._partial(staged)
            original = (staged / "checkpoint.json").read_bytes()
            self.assertEqual(self.store.save(staged, "synthetic-run"), 1)
            # Retry is harmless if the first commit succeeded but ACK was lost.
            self.assertEqual(self.store.save(staged, "synthetic-run"), 1)
            self.assertEqual(
                self.store.restore(
                    restored, "synthetic-run",
                    expected_scope=source.scope, expected_total=2,
                ), 1,
            )
            self.assertEqual((restored / "checkpoint.json").read_bytes(), original)
            self.assertEqual(
                stage_metadata(source, restored, max_pages=1, resume=True)["status"],
                "complete",
            )
            self.assertEqual(
                self.store.save(restored, "synthetic-run", expected_revision=1), 2,
            )
            self.assertEqual(
                self.store.save(restored, "synthetic-run", expected_revision=2), 2,
            )
            self.assertEqual(
                self.store.restore(
                    finished, "synthetic-run",
                    expected_scope=source.scope, expected_total=2,
                ), 2,
            )
            self.assertEqual(
                (finished / "checkpoint.json").read_bytes(),
                (restored / "checkpoint.json").read_bytes(),
            )
            self.assertEqual(
                stage_metadata(source, finished, resume=True)["status"], "complete",
            )
            self.assertEqual(source.requested, [None, "private-synthetic-cursor"])
            self.assertEqual(len(self.db.pages["synthetic-run"]), 2)
            self.assertEqual(len(self.db.artifacts), 2)

    def test_stale_writer_rejected_without_modifying_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "staged"
            source = self._partial(root)
            self.assertEqual(self.store.save(root, "test-run"), 1)
            stage_metadata(source, root, resume=True)
            previous = copy.deepcopy(self.db.checkpoints)
            with self.assertRaisesRegex(PersistenceRejected, "write_conflict"):
                self.store.save(root, "test-run", expected_revision=0)
            self.assertEqual(self.db.checkpoints, previous)

    def test_corrupted_local_artifact_does_not_write_to_db(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "stage"
            self._partial(root)
            digest = json.loads((root / "checkpoint.json").read_text())["pages"][0][
                "artifact_sha256"
            ]
            (root / "raw" / digest[:2] / f"{digest}.json").write_bytes(b"bad")
            with self.assertRaises(StageRejected):
                self.store.save(root, "invalid")
            self.assertFalse(self.db.checkpoints)

    def test_corrupted_remote_artifact_rejected_on_restore(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._partial(root / "staged")
            self.store.save(root / "staged", "test-run")
            digest = next(iter(self.db.artifacts))
            self.db.artifacts[digest] = b"tampered"
            with self.assertRaises(StageRejected):
                self.store.restore(
                    root / "recover", "test-run",
                    expected_scope=source.scope, expected_total=2,
                )
            self.assertFalse((root / "recover").exists())

    def test_corrupted_remote_manifest_and_metadata_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._partial(root / "stage")
            self.store.save(root / "stage", "r")
            row = list(self.db.checkpoints["r"])
            row[3] = b'{"tampered":true}\n'
            self.db.checkpoints["r"] = tuple(row)
            with self.assertRaisesRegex(PersistenceRejected, "digest_invalid"):
                self.store.restore(root / "recover", "r",
                                   expected_scope=source.scope, expected_total=2)

    def test_restore_never_overwrites_existing_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._partial(root / "stage")
            self.store.save(root / "stage", "r")
            dest = root / "recover"
            dest.mkdir()
            (dest / "important.txt").write_text("preserve")
            with self.assertRaisesRegex(PersistenceRejected, "destination_exists"):
                self.store.restore(dest, "r", expected_scope=source.scope,
                                   expected_total=2)
            self.assertEqual((dest / "important.txt").read_text(), "preserve")

    def test_scope_and_total_required_before_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self._partial(root / "stage")
            self.store.save(root / "stage", "r")
            for scope, total in [
                ({"institution": "other"}, 2), (source.scope, 3),
            ]:
                with self.subTest(scope=scope, total=total):
                    with self.assertRaisesRegex(
                        PersistenceRejected, "scope_or_total_mismatch"
                    ):
                        self.store.restore(root / "new", "r",
                                           expected_scope=scope, expected_total=total)
                    self.assertFalse((root / "new").exists())

    def test_failed_transaction_rolls_back_artifacts_and_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "stage"
            self._partial(root)
            self.db.fail_at = "INSERT INTO mar_p0.checkpoints"
            with self.assertRaisesRegex(RuntimeError, "database_disconnection"):
                self.store.save(root, "r")
            self.assertEqual(self.db.artifacts, {})
            self.assertEqual(self.db.checkpoints, {})
            self.assertEqual(self.db.pages, {})
            self.db.fail_at = None
            self.assertEqual(self.store.save(root, "r"), 1)

    def test_reject_non_append_update_even_with_valid_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "staged"
            source = self._partial(root)
            self.store.save(root, "r")
            # Different source, valid new local checkpoint, but not same scope.
            other = Path(directory) / "other"
            another = _Source()
            another.scope["evidence"] = "b" * 64
            stage_metadata(another, other)
            with self.assertRaisesRegex(PersistenceRejected, "not_append_only"):
                self.store.save(other, "r", expected_revision=1)
            self.assertEqual(self.db.checkpoints["r"][0], 1)
            self.assertEqual(source.requested, [None])

    def test_id_cycle_and_deduplication_still_enforced_by_original_runner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "staged"
            source = self._partial(root)
            self.store.save(root, "r")
            class _Repeated(_Source):
                def fetch_page(self, token):
                    if token is not None:
                        previous = super().fetch_page(None)
                        return MetadataPage(previous.records, 2, None, previous.raw)
                    return super().fetch_page(token)
            duplicate = _Repeated()
            with self.assertRaisesRegex(StageRejected, "duplicate_ids_across_pages"):
                stage_metadata(duplicate, root, resume=True)
            self.assertEqual(self.db.checkpoints["r"][0], 1)
            self.assertEqual(source.requested, [None])


if __name__ == "__main__":
    unittest.main()
