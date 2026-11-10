"""Synthetic-only validation of P0 encrypted checkpoint backup and recovery."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from memoria_audiovisual.digital_infrastructure.raw_artifacts import canonical_json_bytes
from memoria_audiovisual.metadata_staging import MetadataPage, stage_metadata
from memoria_audiovisual.p0_encrypted_backup import (
    BackupRejected,
    _AAD,
    _VERSION,
    _b64,
    _key,
    decrypt_staging,
    encrypt_staging,
)


_SECRET = b"synthetic-test-only-passphrase-at-least-16-bytes"


class SyntheticSource:
    scope = {"institution": "synthetic-p0-only", "evidence": "a" * 64}

    def preflight(self) -> int:
        return 2

    def fetch_page(self, token: str | None) -> MetadataPage:
        if token is None:
            record, next_token = {"id": "synthetic-001"}, "opaque-test-cursor"
        elif token == "opaque-test-cursor":
            record, next_token = {"id": "synthetic-002"}, None
        else:
            raise AssertionError("unexpected cursor")
        return MetadataPage(
            (record,), 2, next_token,
            {"status": "OK", "records": [record]},
        )


class EncryptedBackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sandbox = tempfile.TemporaryDirectory(prefix="mar-p0-encrypted-")
        self.addCleanup(self.sandbox.cleanup)
        self.root = Path(self.sandbox.name)
        self.source = SyntheticSource()
        self.staged = self.root / "staged"
        self.archive = self.root / "checkpoint.marp0.enc"
        self.recovered = self.root / "recovered"
        stage_metadata(self.source, self.staged, max_pages=1)

    def test_encrypt_restore_and_resume_original_runner(self):
        encrypt_staging(self.staged, self.archive, _SECRET)
        self.assertNotIn(b"opaque-test-cursor", self.archive.read_bytes())
        self.assertNotIn(b"synthetic-001", self.archive.read_bytes())
        decrypt_staging(self.archive, self.recovered, _SECRET)
        self.assertEqual(
            (self.staged / "checkpoint.json").read_bytes(),
            (self.recovered / "checkpoint.json").read_bytes(),
        )
        raw = list((self.staged / "raw").rglob("*.json"))
        self.assertEqual(len(raw), 1)
        self.assertEqual(
            raw[0].read_bytes(),
            (self.recovered / raw[0].relative_to(self.staged)).read_bytes(),
        )
        self.assertEqual(
            stage_metadata(self.source, self.recovered, resume=True)["status"],
            "complete",
        )

    def test_wrong_secret_rejects_without_creating_destination(self):
        encrypt_staging(self.staged, self.archive, _SECRET)
        with self.assertRaisesRegex(BackupRejected, "integrity_or_secret"):
            decrypt_staging(self.archive, self.recovered, b"wrong-secret-value-123")
        self.assertFalse(self.recovered.exists())

    def test_ciphertext_tampering_does_not_restore(self):
        encrypt_staging(self.staged, self.archive, _SECRET)
        payload = json.loads(self.archive.read_bytes())
        encrypted = bytearray(base64.b64decode(payload["ciphertext"]))
        encrypted[-1] ^= 1
        payload["ciphertext"] = _b64(bytes(encrypted))
        self.archive.write_bytes(canonical_json_bytes(payload) + b"\n")
        with self.assertRaisesRegex(BackupRejected, "integrity_or_secret"):
            decrypt_staging(self.archive, self.recovered, _SECRET)
        self.assertFalse(self.recovered.exists())

    def test_backup_never_overwrites_existing_archive(self):
        self.archive.write_bytes(b"original")
        with self.assertRaisesRegex(BackupRejected, "destination_exists"):
            encrypt_staging(self.staged, self.archive, _SECRET)
        self.assertEqual(self.archive.read_bytes(), b"original")

    def test_restore_never_overwrites_existing_files(self):
        encrypt_staging(self.staged, self.archive, _SECRET)
        self.recovered.mkdir()
        (self.recovered / "important").write_text("preserve")
        with self.assertRaisesRegex(BackupRejected, "destination_exists"):
            decrypt_staging(self.archive, self.recovered, _SECRET)
        self.assertEqual((self.recovered / "important").read_text(), "preserve")

    def test_refuses_symlinks_and_unrelated_files(self):
        unrelated = self.staged / "not-metadata.txt"
        unrelated.write_text("unrelated")
        with self.assertRaisesRegex(BackupRejected, "unexpected_file"):
            encrypt_staging(self.staged, self.archive, _SECRET)
        unrelated.unlink()
        try:
            (self.staged / "other-link").symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks not available")
        with self.assertRaisesRegex(BackupRejected, "symlink_refused"):
            encrypt_staging(self.staged, self.archive, _SECRET)

    def test_missing_original_artifact_cannot_be_backed_up(self):
        for path in (self.staged / "raw").rglob("*.json"):
            path.unlink()
        with self.assertRaisesRegex(BackupRejected, "artifact_missing"):
            encrypt_staging(self.staged, self.archive, _SECRET)

    def test_authenticated_traversal_payload_refused(self):
        nonce, salt = os.urandom(12), os.urandom(16)
        forged = canonical_json_bytes({
            "version": _VERSION,
            "files": [{
                "path": "../unsafe.json",
                "sha256": hashlib.sha256(b"payload").hexdigest(),
                "data": _b64(b"payload"),
            }],
        })
        ciphertext = AESGCM(_key(_SECRET, salt)).encrypt(nonce, forged, _AAD)
        self.archive.write_bytes(canonical_json_bytes({
            "version": _VERSION, "salt": _b64(salt),
            "nonce": _b64(nonce), "ciphertext": _b64(ciphertext),
        }) + b"\n")
        with self.assertRaisesRegex(BackupRejected, "path_invalid"):
            decrypt_staging(self.archive, self.recovered, _SECRET)
        self.assertFalse(self.recovered.exists())


if __name__ == "__main__":
    unittest.main()
