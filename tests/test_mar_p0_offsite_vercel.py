"""Offline verification of MAR P0 Vercel private Blob ciphertext transport."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from scripts.mar_p0_offsite_vercel import (
    BackupRejected, MAGIC, assert_cipher, assert_private_file,
    choose_older_blob, fetch_private, main, put_private, read_from_private_blob,
    token_from, digest, PREFIX,
)

NOW = datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc)
BLOB = MAGIC + b"synthetic-encrypted-ciphertext" * 7
SHA = hashlib.sha256(BLOB).hexdigest()
TOKEN = "test-token-only-not-real-credential"
RUN_ID = "43295473787"


class FakePrivateBlob:
    def __init__(self):
        self.records = {}
        self.put_calls = []

    async def put(self, pathname, blob, **kwargs):
        self.put_calls.append(kwargs)
        if pathname in self.records or kwargs["overwrite"] is not False:
            raise BackupRejected("overwrite_refused")
        assert kwargs["access"] == "private"
        assert kwargs["add_random_suffix"] is False
        assert kwargs["token"] == TOKEN
        self.records[pathname] = bytes(blob)
        return SimpleNamespace(pathname=pathname, url=(
            "https://private123.private.blob.vercel-storage.com/" + pathname))

    async def get(self, pathname, **kwargs):
        assert kwargs["access"] == "private"
        assert kwargs["token"] == TOKEN
        if pathname not in self.records:
            return None

        async def stream():
            yield self.records[pathname][:30]
            yield self.records[pathname][30:]

        return SimpleNamespace(
            status_code=200, stream=stream(),
            blob=SimpleNamespace(pathname=pathname),
        )


def item(path, age_h):
    return SimpleNamespace(pathname=path, uploaded_at=NOW-timedelta(hours=age_h))


class VercelPrivateArchiveTests(unittest.TestCase):
    def setUp(self):
        self.client = FakePrivateBlob()

    def _upload(self, root):
        path = Path(root) / "backup.aesgcm"
        path.write_bytes(BLOB)
        record = asyncio.run(put_private(
            self.client, path, SHA, RUN_ID, "1", TOKEN, now=NOW))
        return path, record

    def test_dry_run_never_authenticates_or_touches_blob(self):
        with patch("scripts.mar_p0_offsite_vercel.token_from") as tokens:
            self.assertEqual(main(["upload", "--encrypted-file", "/not-found"]), 0)
        tokens.assert_not_called()

    def test_token_is_required_for_protected_storage(self):
        with self.assertRaises(BackupRejected):
            token_from({})
        self.assertEqual(token_from({"MAR_P0_VERCEL_BLOB_READ_WRITE_TOKEN": TOKEN}), TOKEN)

    def test_only_authenticated_private_ciphertext_is_uploaded(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, record = self._upload(root)
            self.assertEqual(record["status"], "private_ciphertext_uploaded_and_readback_verified")
            self.assertEqual(record["sha256"], SHA)
            self.assertFalse(record["provider_retention_enforced"])
            self.assertEqual(record["production_gate"], "HOLD")
            kwargs = self.client.put_calls[0]
            self.assertEqual(kwargs["access"], "private")
            self.assertIs(kwargs["overwrite"], False)
            self.assertEqual(kwargs["token"], TOKEN)
            self.assertEqual(self.client.records[record["pathname"]], BLOB)

    def test_upload_rejects_plaintext_wrong_hash_and_invalid_run(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            source = Path(root) / "backup.aesgcm"
            for raw, sha, run_id in ((b"PGDMP"+"x".encode()*100, SHA, RUN_ID),
                                     (BLOB, "0"*64, RUN_ID),
                                     (BLOB, SHA, "../malicious")):
                with self.subTest(raw=raw[:5], run_id=run_id):
                    source.write_bytes(raw)
                    with self.assertRaises(BackupRejected):
                        asyncio.run(put_private(self.client, source, sha,
                                                run_id, "1", TOKEN, now=NOW))
            self.assertEqual(self.client.records, {})

    def test_duplicate_key_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            source, record = self._upload(root)
            with self.assertRaises(BackupRejected):
                asyncio.run(put_private(
                    self.client, source, SHA, RUN_ID, "1", TOKEN, now=NOW))
            self.assertEqual(self.client.records[record["pathname"]], BLOB)

    def test_download_requires_expected_sha_and_valid_path(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, record = self._upload(root)
            out = Path(root) / "restored.aesgcm"
            with self.assertRaises(BackupRejected):
                asyncio.run(fetch_private(
                    self.client, out, TOKEN,
                    pathname=record["pathname"], expected="0"*64))
            self.assertFalse(out.exists())
            with self.assertRaises(BackupRejected):
                asyncio.run(read_from_private_blob(
                    self.client, "../other", TOKEN))

    def test_download_roundtrip_and_private_file_mode(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, record = self._upload(root)
            target = Path(root) / "restored.aesgcm"
            recovered = asyncio.run(fetch_private(
                self.client, target, TOKEN,
                pathname=record["pathname"], expected=SHA))
            self.assertEqual(recovered["status"], "private_ciphertext_download_verified")
            self.assertEqual(target.read_bytes(), BLOB)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(BackupRejected):
                asyncio.run(fetch_private(
                    self.client, target, TOKEN,
                    pathname=record["pathname"], expected=SHA))

    def test_download_detects_mutated_cipher(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, record = self._upload(root)
            self.client.records[record["pathname"]] = BLOB[:-1] + b"Z"
            with self.assertRaises(BackupRejected):
                asyncio.run(fetch_private(
                    self.client, Path(root)/"new", TOKEN,
                    pathname=record["pathname"], expected=SHA))

    def test_download_rejects_unprotected_directory(self):
        if os.name != "posix":
            return
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o755)
            with self.assertRaises(BackupRejected):
                assert_private_file(Path(root)/"x", exists=False)

    def test_weekly_selector_only_24_to_192_hours(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, record = self._upload(root)
            key = record["pathname"]
            data = [item(key, 12), item(key, 40), item(key, 200),
                    item("not_mar_p0/other", 30)]
            pathname, sha = choose_older_blob(data, now=NOW)
            self.assertEqual((pathname, sha), (key, SHA))

    def test_no_older_backup_is_a_failed_recovery(self):
        with self.assertRaises(BackupRejected):
            choose_older_blob([], now=NOW)
        with self.assertRaises(BackupRejected):
            choose_older_blob([item(PREFIX+"x", 50)], now=NOW)

    def test_invalid_sha_or_truncation_refused(self):
        with self.assertRaises(BackupRejected):
            assert_cipher(BLOB, "0"*64)
        with self.assertRaises(BackupRejected):
            assert_cipher(BLOB[:12], SHA)
        self.assertEqual(digest(BLOB), SHA)

    def test_prevents_network_access_from_unit_suite(self):
        with patch("scripts.mar_p0_offsite_vercel.token_from") as get_token:
            self.assertEqual(main(["download", "--encrypted-file", "/none"]), 0)
            get_token.assert_not_called()


if __name__ == "__main__":
    unittest.main()
