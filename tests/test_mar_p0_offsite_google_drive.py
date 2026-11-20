"""Offline adversarial tests for Drive-only F02 encrypted backup transport."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch
import sys

from scripts.mar_p0_offsite_google_drive import (
    DriveBackupRejected, FILE_MIME, FOLDER_MIME, MAGIC,
    check_cipher, download, main, new_name, select_older,
    upload, verify_folder, verify_oauth_scopes, SCOPE,
)

UTC = timezone.utc
NOW = datetime(2026, 11, 19, 20, 0, tzinfo=UTC)
FOLDER = "folder_test_AAAAAAAAAAAAAAAAA"
FILE_ID = "file_test_BBBBBBBBBBBBBBBBBB"
SHA = hashlib.sha256(MAGIC + b"\x00" * 200).hexdigest()
RAW = MAGIC + b"\x00" * 200
NAME = new_name(SHA, run_id="12345", attempt="1", now=NOW)


class FakeCall:
    def __init__(self, value):
        self.value = value

    def execute(self):
        return self.value


class FakeDriveFiles:
    def __init__(self):
        self.raw = RAW
        self.file = {
            "id": FILE_ID, "name": NAME, "mimeType": FILE_MIME,
            "parents": [FOLDER], "trashed": False,
            "size": str(len(RAW)), "createdTime": (NOW - timedelta(hours=48)).isoformat(),
            "appProperties": {"sha256": SHA},
        }
        self.folder = {"id": FOLDER, "mimeType": FOLDER_MIME,
                       "shared": False, "trashed": False}
        self.next_token = None
        self.items = [self.file]
        self.created = 0

    def files(self):
        return self

    def get(self, fileId, fields):
        return FakeCall(self.folder if fileId == FOLDER else self.file)

    def get_media(self, fileId):
        return FakeCall(self.raw)

    def list(self, **kwargs):
        if self.next_token is not None and "pageToken" not in kwargs:
            return FakeCall({"files": [], "nextPageToken": self.next_token})
        return FakeCall({"files": self.items})

    def create(self, body, media_body, fields):
        self.created += 1
        self.raw = media_body.contents
        self.file = {
            "id": FILE_ID, "name": body["name"],
            "mimeType": FILE_MIME, "parents": [FOLDER],
            "trashed": False, "size": str(len(self.raw)),
            "createdTime": NOW.isoformat(), "appProperties": body["appProperties"],
        }
        return FakeCall({"id": FILE_ID})


class FakeUploadMedia:
    def __init__(self, stream, mimetype, resumable, chunksize):
        self.contents = stream.getvalue()


class DriveCipherTransportTests(unittest.TestCase):
    def test_default_is_offline_dry_run(self):
        with patch("scripts.mar_p0_offsite_google_drive.get_service") as auth:
            result = main(["upload", "--encrypted-file", "/unused",
                           "--receipt-file", "/unused/receipt"])
        self.assertEqual(result, 0)
        auth.assert_not_called()

    def test_encrypted_only_and_strict_sha(self):
        check_cipher(RAW, SHA)
        for bad, pin in ((b"plaintext" * 40, hashlib.sha256(b"plaintext" * 40).hexdigest()),
                         (RAW[:-1] + b"x", SHA), (RAW, "0" * 64)):
            with self.subTest(pin=pin), self.assertRaises(DriveBackupRejected):
                check_cipher(bad, pin)

    def test_invalid_run_id_and_clock_rejected(self):
        for run_id in ("x", "1", "1/../2", ""):
            with self.assertRaises(DriveBackupRejected):
                new_name(SHA, run_id=run_id, attempt="1", now=NOW)
        with self.assertRaises(DriveBackupRejected):
            new_name(SHA, run_id="1234", attempt="1", now=NOW.replace(tzinfo=None))

    def test_drive_folder_must_be_private(self):
        fake = FakeDriveFiles()
        verify_folder(fake, FOLDER)
        fake.folder["shared"] = True
        with self.assertRaises(DriveBackupRejected):
            verify_folder(fake, FOLDER)

    def test_prior_selection_age_and_metadata_and_no_secret_leak(self):
        fake = FakeDriveFiles()
        selected = select_older(fake, folder_id=FOLDER, now=NOW)
        self.assertEqual(selected["sha256"], SHA)
        fake.items[0]["appProperties"] = {"sha256": "0" * 64}
        with self.assertRaises(DriveBackupRejected):
            select_older(fake, folder_id=FOLDER, now=NOW)
        fake.items[0]["appProperties"] = {"sha256": SHA}
        with self.assertRaises(DriveBackupRejected):
            select_older(fake, folder_id=FOLDER, now=NOW, min_age_hours=72, max_age_hours=192)

    def test_oauth_scope_validation_allows_omitted_scope_if_request_exact(self):
        # Google OAuth refresh may omit granted_scopes when same as requested.
        verify_oauth_scopes(types.SimpleNamespace(scopes=[SCOPE], granted_scopes=None, valid=True))
        verify_oauth_scopes(types.SimpleNamespace(scopes=[SCOPE], granted_scopes=[], valid=True))
        verify_oauth_scopes(types.SimpleNamespace(scopes=[SCOPE], granted_scopes=[SCOPE], valid=True))
        for credentials in (
            types.SimpleNamespace(scopes=[SCOPE], granted_scopes=[SCOPE, "https://www.googleapis.com/auth/drive"], valid=True),
            types.SimpleNamespace(scopes=["https://www.googleapis.com/auth/drive"], granted_scopes=None, valid=True),
            types.SimpleNamespace(scopes=[SCOPE], granted_scopes=[SCOPE], valid=False),
        ):
            with self.subTest(creds=credentials), self.assertRaises(DriveBackupRejected):
                verify_oauth_scopes(credentials)

    def test_independent_restore_selects_exact_digest_not_newest_unrelated_backup(self):
        fake = FakeDriveFiles()
        newest = dict(fake.file)
        newest["id"] = "newest_file_CCCCCCCCCCCCCCCCC"
        newest["createdTime"] = (NOW - timedelta(hours=25)).isoformat()
        newest["name"] = new_name("a" * 64, run_id="12345", attempt="1", now=NOW)
        newest["appProperties"] = {"sha256": "a" * 64}
        fake.items = [newest, fake.file]
        selected = select_older(fake, folder_id=FOLDER, now=NOW, expected_sha=SHA)
        self.assertEqual(selected["sha256"], SHA)
        self.assertEqual(selected["file_id"], FILE_ID)
        with self.assertRaises(DriveBackupRejected):
            select_older(fake, folder_id=FOLDER, now=NOW, expected_sha="b" * 64)
        with self.assertRaises(DriveBackupRejected):
            select_older(fake, folder_id=FOLDER, now=NOW, expected_sha="not-a-hash")

    def test_decrypt_is_not_attempted_during_transport_and_restore_target_exclusive(self):
        fake = FakeDriveFiles()
        receipt = select_older(fake, folder_id=FOLDER, now=NOW)
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            folder.chmod(0o700)
            target = folder / "restored.aesgcm"
            report = download(fake, receipt=receipt, target=target, folder_id=FOLDER)
            self.assertEqual(report["sha256"], SHA)
            self.assertEqual(target.read_bytes(), RAW)
            with self.assertRaises(DriveBackupRejected):
                download(fake, receipt=receipt, target=target, folder_id=FOLDER)

    def test_cross_folder_or_modified_remote_file_is_rejected(self):
        fake = FakeDriveFiles()
        receipt = select_older(fake, folder_id=FOLDER, now=NOW)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.enc"
            with self.assertRaises(DriveBackupRejected):
                download(fake, receipt={**receipt, "folder_id": "other_Folder_AAAAAAAAAAA"},
                         target=p, folder_id=FOLDER)
            fake.file["parents"] = ["outside_dir_AAAAAAAAAAAAAA"]
            with self.assertRaises(DriveBackupRejected):
                download(fake, receipt=receipt, target=p, folder_id=FOLDER)
            fake.file["parents"] = [FOLDER]
            fake.raw = RAW[:-1] + b"x"
            with self.assertRaises(DriveBackupRejected):
                download(fake, receipt=receipt, target=p, folder_id=FOLDER)

    def test_ciphertext_upload_download_readback_offline(self):
        fake = FakeDriveFiles()
        pkg = types.ModuleType("googleapiclient")
        http = types.ModuleType("googleapiclient.http")
        http.MediaIoBaseUpload = FakeUploadMedia
        pkg.http = http
        with tempfile.TemporaryDirectory() as d:
            folder = Path(d)
            folder.chmod(0o700)
            source = folder / "cipher.aesgcm"
            source.write_bytes(RAW)
            with patch.dict(sys.modules, {"googleapiclient": pkg, "googleapiclient.http": http}):
                receipt = upload(fake, folder_id=FOLDER, path=source, expected_sha=SHA,
                                 run_id="12345", attempt="1", now=NOW)
            self.assertTrue(receipt["verified"])
            self.assertFalse(receipt["worm_proven"])
            self.assertEqual(fake.created, 1)
            self.assertEqual(fake.raw, RAW)
            self.assertEqual(fake.file["name"], NAME)

    def test_main_fails_closed_without_oauth_or_folder_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            code = main(["upload", "--execute", "--encrypted-file", "/unused",
                         "--receipt-file", str(Path(d) / "receipt")], env={})
        self.assertEqual(code, 2)

    def test_invalid_receipt_sha_is_rejected_before_file_created(self):
        fake = FakeDriveFiles()
        receipt = select_older(fake, folder_id=FOLDER, now=NOW)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.enc"
            with self.assertRaises(DriveBackupRejected):
                download(fake, receipt={**receipt, "sha256": "0" * 64},
                         target=p, folder_id=FOLDER)
            self.assertFalse(p.exists())


if __name__ == "__main__":
    unittest.main()
