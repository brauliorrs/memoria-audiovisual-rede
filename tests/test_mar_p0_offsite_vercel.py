"""Offline interface and safety tests for the official vercel-blob 0.5.1 SDK."""
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
    check_auth, choose_older_blob, download_private, main,
    read_private, upload_private, digest, PREFIX, find_prior,
)

NOW = datetime(2026, 11, 13, 20, 0, tzinfo=timezone.utc)
BLOB = MAGIC + b"synthetic-encrypted-ciphertext" * 7
SHA = hashlib.sha256(BLOB).hexdigest()
TOKEN = "synthetic-test-credential-never-real"
RUN_ID = "43295473787"


class FakeVercelSDK:
    """Implements the public vercel.blob interface, not a private client API."""

    def __init__(self):
        self.records = {}
        self.put_calls = []
        self.times = {}

    async def put_blob(self, pathname, data, **kwargs):
        self.put_calls.append(kwargs)
        if pathname in self.records:
            raise BackupRejected("overwrite_refused")
        assert kwargs["access"] == "private"
        assert kwargs["allow_overwrite"] is False
        assert kwargs["add_random_suffix"] is False
        self.records[pathname] = bytes(data)
        self.times[pathname] = NOW
        return SimpleNamespace(
            pathname=pathname,
            url="https://private123.private.blob.vercel-storage.com/" + pathname,
        )

    async def get_blob(self, pathname, *, access):
        assert access == "private"
        if pathname not in self.records:
            return None
        return SimpleNamespace(
            metadata=SimpleNamespace(status_code=200),
            body=self.records[pathname],
        )

    async def query_blobs(self, *, prefix, page_size):
        assert prefix == PREFIX and page_size == 100
        for pathname in self.records:
            yield SimpleNamespace(pathname=pathname, uploaded_at=self.times[pathname])


def item(path, age_h):
    return SimpleNamespace(
        pathname=path, uploaded_at=NOW - timedelta(hours=age_h)
    )


class PrivateVercelArchiveTests(unittest.TestCase):
    def setUp(self):
        self.sdk = FakeVercelSDK()

    def upload(self, directory):
        path = Path(directory) / "snapshot.aesgcm"
        path.write_bytes(BLOB)
        info = asyncio.run(
            upload_private(self.sdk, path, SHA, RUN_ID, "1", now=NOW)
        )
        return path, info

    def test_dry_run_never_accesses_auth_or_network(self):
        with patch("scripts.mar_p0_offsite_vercel.check_auth") as checker:
            self.assertEqual(main(["upload", "--encrypted-file", "/missing"]), 0)
        checker.assert_not_called()

    def test_token_is_required_and_not_logged(self):
        with self.assertRaises(BackupRejected):
            check_auth({})
        check_auth({"BLOB_READ_WRITE_TOKEN": TOKEN})
        with self.assertRaises(BackupRejected):
            check_auth({"BLOB_READ_WRITE_TOKEN": "short"})

    def test_private_ciphertext_upload_and_authenticated_readback(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            self.assertEqual(
                result["status"], "private_ciphertext_uploaded_and_readback_verified"
            )
            self.assertEqual(result["sha256"], SHA)
            self.assertFalse(result["provider_retention_enforced"])
            self.assertEqual(result["production_gate"], "HOLD")
            self.assertEqual(self.sdk.records[result["pathname"]], BLOB)
            self.assertEqual(self.sdk.put_calls[0]["access"], "private")
            self.assertIs(self.sdk.put_calls[0]["allow_overwrite"], False)

    def test_invalid_source_and_hash_rejected_before_upload(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            source = Path(root) / "bad.aesgcm"
            cases = [(b"PGDMP" + b"x" * 200, SHA, RUN_ID),
                     (BLOB, "0" * 64, RUN_ID),
                     (BLOB, SHA, "../malicious")]
            for payload, sha, run_id in cases:
                with self.subTest(payload=payload[:5], run_id=run_id):
                    source.write_bytes(payload)
                    with self.assertRaises(BackupRejected):
                        asyncio.run(upload_private(
                            self.sdk, source, sha, run_id, "1", now=NOW
                        ))
            self.assertEqual(self.sdk.records, {})

    def test_repeated_upload_cannot_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            source, result = self.upload(root)
            with self.assertRaises(BackupRejected):
                asyncio.run(upload_private(
                    self.sdk, source, SHA, RUN_ID, "1", now=NOW
                ))
            self.assertEqual(self.sdk.records[result["pathname"]], BLOB)

    def test_tampered_remote_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            self.sdk.records[result["pathname"]] = BLOB[:-1] + b"Z"
            with self.assertRaises(BackupRejected):
                asyncio.run(download_private(
                    self.sdk, Path(root) / "new.aesgcm",
                    pathname=result["pathname"], expected=SHA
                ))

    def test_download_requires_valid_location_and_independent_sha(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            with self.assertRaises(BackupRejected):
                asyncio.run(download_private(
                    self.sdk, Path(root) / "new.aesgcm",
                    pathname=result["pathname"], expected="0" * 64
                ))
            with self.assertRaises(BackupRejected):
                asyncio.run(read_private(self.sdk, "../other"))
            self.assertFalse((Path(root) / "new.aesgcm").exists())

    def test_download_roundtrip_preserves_mode_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            destination = Path(root) / "download.aesgcm"
            verified = asyncio.run(download_private(
                self.sdk, destination,
                pathname=result["pathname"], expected=SHA
            ))
            self.assertEqual(verified["status"], "private_ciphertext_download_verified")
            self.assertEqual(destination.read_bytes(), BLOB)
            if os.name == "posix":
                self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(BackupRejected):
                asyncio.run(download_private(
                    self.sdk, destination,
                    pathname=result["pathname"], expected=SHA
                ))

    def test_unprotected_download_directory_is_rejected(self):
        if os.name != "posix":
            self.skipTest("Unix-only directory mode")
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o755)
            with self.assertRaises(BackupRejected):
                assert_private_file(Path(root) / "new", exists=False)

    def test_prior_version_selection_is_time_bounded(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            path = result["pathname"]
            values = [item(path, 12), item(path, 40),
                      item(path, 200), item("other/secret", 30)]
            self.assertEqual(
                choose_older_blob(values, now=NOW), (path, SHA)
            )

    def test_listing_sdk_async_iterator_selects_old_entry(self):
        with tempfile.TemporaryDirectory() as root:
            os.chmod(root, 0o700)
            _, result = self.upload(root)
            self.sdk.times[result["pathname"]] = NOW - timedelta(hours=35)
            selected = asyncio.run(find_prior(
                self.sdk, now=NOW, min_age_hours=24, max_age_hours=192
            ))
            self.assertEqual(selected, (result["pathname"], SHA))

    def test_no_old_backup_is_a_failed_recovery(self):
        with self.assertRaises(BackupRejected):
            choose_older_blob([], now=NOW)
        with self.assertRaises(BackupRejected):
            asyncio.run(find_prior(
                self.sdk, now=NOW, min_age_hours=24, max_age_hours=192
            ))

    def test_wrong_digest_and_truncation_rejected(self):
        with self.assertRaises(BackupRejected):
            assert_cipher(BLOB, "0" * 64)
        with self.assertRaises(BackupRejected):
            assert_cipher(BLOB[:12], SHA)
        self.assertEqual(digest(BLOB), SHA)


if __name__ == "__main__":
    unittest.main()
