"""P0 pre-registered offline secret-checkpoint backup and restore tests.

Committed before the encryption implementation. Synthetic Finna metadata only:
no media, network, repository secrets, public artifacts or real provider tokens.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.kavi_finna_adapter import FinnaScope
from memoria_audiovisual.metadata_staging import MetadataPage, stage_metadata
from memoria_audiovisual.kavi_finna_secure_backup import (
    BackupRejected, backup_verified_epoch, restore_verified_epoch,
    load_backup_key_from_environment,
)
from scripts.audit_kavi_finna_staging import audit_finna_staging

EVIDENCE = "a" * 64
CURSOR = "private-synthetic-checkpoint-token-01234"
KEY = bytes(range(32))
WRONG_KEY = b"x" * 32


class SyntheticFinnaSource:
    def __init__(self):
        self.scope = FinnaScope("0/KAVI/", "0/Video/", EVIDENCE).to_dict()
        self.calls = []

    def preflight(self):
        return 3

    def fetch_page(self, token):
        self.calls.append(token)
        if token is not None:
            raise AssertionError("restore must never call provider")
        record = {
            "id": "kavi.elonet_elokuva_synthetic_001",
            "title": "Synthetic metadata record only",
            "formats": [{"value": "0/Video/"}],
            "provider_index_code": "0/KAVI/",
            "custody_status": "not_established",
            "media_rights_status": "not_verified",
            "media_downloaded": False,
            "film_semantics": "film_candidate",
        }
        return MetadataPage(
            (record,), 3, CURSOR,
            {"status": "OK", "resultCount": 3,
             "records": [{"id": record["id"], "title": record["title"]}],
             "resumptionToken": {
                 "token": CURSOR, "expires": "2030-01-01T00:00:00Z",
             }},
        )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SecureCheckpointBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        home = Path(self.temp.name)
        self.source = home / "private-stage"
        self.source.mkdir(mode=0o700)
        self.archive_home = home / "private-backups"
        self.archive_home.mkdir(mode=0o700)
        self.archive = self.archive_home / "epoch-0001.kavienc"
        self.restore_home = home / "private-restore"
        self.restore_home.mkdir(mode=0o700)
        self.restored = self.restore_home / "epoch-0001"
        self.source_adapter = SyntheticFinnaSource()
        staged = stage_metadata(self.source_adapter, self.source, max_pages=1)
        self.assertEqual(staged["record_count"], 1)
        self.assertEqual(staged["status"], "partial")
        self.assertEqual(self.source_adapter.calls, [None])
        self.original = {
            p.relative_to(self.source).as_posix(): digest(p)
            for p in self.source.rglob("*") if p.is_file()
        }

    def backup(self, **changes):
        kwargs = {
            "evidence_sha256": EVIDENCE,
            "expected_total": 3,
            "epoch_id": "epoch-0001",
            "key": KEY,
        }
        kwargs.update(changes)
        return backup_verified_epoch(self.source, self.archive, **kwargs)

    def restore(self, **changes):
        kwargs = {
            "evidence_sha256": EVIDENCE,
            "expected_total": 3,
            "epoch_id": "epoch-0001",
            "key": KEY,
        }
        kwargs.update(changes)
        return restore_verified_epoch(self.archive, self.restored, **kwargs)

    def test_p01_backup_and_restore_across_independent_directories(self):
        report = self.backup()
        self.assertEqual(report["record_count"], 1)
        self.assertEqual(report["page_count"], 1)
        self.assertEqual(report["status"], "encrypted")
        self.assertFalse(report["media_downloaded"])
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["durability_verified"])
        self.assertEqual(self.source_adapter.calls, [None])
        restored = self.restore()
        self.assertEqual(restored["status"], "restored_and_audited")
        self.assertEqual(restored["record_count"], 1)
        self.assertTrue(restored["offline_integrity_verified"])
        self.assertFalse(restored["durability_verified"])
        self.assertEqual(self.source_adapter.calls, [None])
        audit = audit_finna_staging(
            self.restored, evidence_sha256=EVIDENCE, expected_total=3,
        )
        self.assertEqual(audit["status"], "partial")
        self.assertEqual(audit["record_count"], 1)
        self.assertEqual(
            digest(self.source / "checkpoint.json"),
            digest(self.restored / "checkpoint.json"),
        )
        self.assertEqual(
            sorted(digest(x) for x in (self.source / "raw").rglob("*.json")),
            sorted(digest(x) for x in (self.restored / "raw").rglob("*.json")),
        )

    def test_p02_confidentiality_and_posix_modes(self):
        self.backup()
        data = self.archive.read_bytes()
        self.assertNotIn(CURSOR.encode(), data)
        self.assertNotIn(b"Synthetic metadata record only", data)
        self.assertNotIn(b"kavi.elonet_elokuva_synthetic_001", data)
        if os.name == "posix":
            self.assertEqual(self.archive.stat().st_mode & 0o777, 0o600)
            self.restore()
            self.assertEqual(self.restored.stat().st_mode & 0o777, 0o700)
            for path in self.restored.rglob("*"):
                self.assertEqual(
                    path.stat().st_mode & 0o777,
                    0o700 if path.is_dir() else 0o600,
                )

    def test_p03_wrong_key_and_invalid_length_fail_closed(self):
        with self.assertRaises(BackupRejected):
            self.backup(key=b"short")
        self.assertFalse(self.archive.exists())
        self.backup()
        with self.assertRaises(BackupRejected):
            self.restore(key=WRONG_KEY)
        self.assertFalse(self.restored.exists())

    def test_p04_corrupt_checkpoint_raw_and_independent_anchors(self):
        for overrides in (
            {"evidence_sha256": "b" * 64}, {"expected_total": 4},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(Exception):
                    self.backup(**overrides)
                self.assertFalse(self.archive.exists())
        raw = next((self.source / "raw").rglob("*.json"))
        raw.write_bytes(raw.read_bytes() + b"forged")
        with self.assertRaises(Exception):
            self.backup()
        self.assertFalse(self.archive.exists())

    def test_p05_ciphertext_header_and_truncation_detected(self):
        self.backup()
        original = self.archive.read_bytes()
        for tampered in (
            original[:-1] + bytes([original[-1] ^ 1]),
            original[:-15],
            original[:12] + bytes([original[12] ^ 1]) + original[13:],
        ):
            self.archive.write_bytes(tampered)
            with self.assertRaises(BackupRejected):
                self.restore()
            self.assertFalse(self.restored.exists())
        self.archive.write_bytes(original)

    def test_p06_load_key_from_env_only_and_no_secret_prints(self):
        import base64
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BackupRejected):
                load_backup_key_from_environment()
        with patch.dict(os.environ, {
            "MAR_KAVI_BACKUP_KEY_B64": base64.b64encode(KEY).decode("ascii"),
        }, clear=True):
            self.assertEqual(load_backup_key_from_environment(), KEY)

    def test_p07_reject_public_permissions_and_symlink(self):
        if os.name != "posix":
            self.skipTest("POSIX permission gate")
        self.source.chmod(0o755)
        with self.assertRaises(BackupRejected):
            self.backup()
        self.assertFalse(self.archive.exists())
        self.source.chmod(0o700)
        self.archive_home.chmod(0o755)
        with self.assertRaises(BackupRejected):
            self.backup()
        self.archive_home.chmod(0o700)
        target = self.archive_home / "untrusted"
        target.write_text("external data")
        self.archive.symlink_to(target)
        with self.assertRaises(BackupRejected):
            self.backup()
        self.archive.unlink()

    def test_p08_refuse_existing_backup_and_restore(self):
        self.backup()
        first_sha = digest(self.archive)
        with self.assertRaises(BackupRejected):
            self.backup()
        self.assertEqual(digest(self.archive), first_sha)
        self.restored.mkdir()
        with self.assertRaises(BackupRejected):
            self.restore()
        self.assertTrue(self.restored.is_dir())

    def test_p09_epoch_and_total_fingerprint_binding(self):
        self.backup()
        for overrides in (
            {"epoch_id": "epoch-0002"},
            {"expected_total": 2},
            {"evidence_sha256": "b" * 64},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(BackupRejected):
                    self.restore(**overrides)
                self.assertFalse(self.restored.exists())

    def test_p10_failed_backup_and_restore_are_not_partially_materialized(self):
        self.backup()
        bad = self.archive.read_bytes()
        self.archive.write_bytes(bad[:-12])
        with self.assertRaises(BackupRejected):
            self.restore()
        self.assertFalse(self.restored.exists())
        self.assertFalse(list(self.restore_home.glob(".kavi-restore-*")))
        self.archive.unlink()
        with self.assertRaises(BackupRejected):
            self.backup(expected_total=-1)
        self.assertFalse(self.archive.exists())
        self.assertFalse(list(self.archive_home.glob("*.tmp")))

    def test_p11_p12_source_invariant_and_no_video_export(self):
        self.backup()
        self.restore()
        before = {
            p.relative_to(self.source).as_posix(): digest(p)
            for p in self.source.rglob("*") if p.is_file()
        }
        self.assertEqual(self.original, before)
        cfg = CORPORA["kavi_kuvi"]
        self.assertFalse(cfg["organism_active"])
        self.assertFalse(cfg["monthly_refresh_enabled"])
        self.assertFalse(cfg["counts_as_analyzed_corpus"])
        self.assertFalse(cfg["metadata_item_links_not_playback"] is False)
        self.assertNotIn(b".mp4", self.archive.read_bytes())


if __name__ == "__main__":
    unittest.main()
