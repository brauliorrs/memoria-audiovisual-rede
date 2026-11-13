"""Offline fail-closed tests for the MAR P0 independent immutable archive."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.mar_p0_offsite_pg_restore import _seal
from scripts.mar_p0_offsite_s3 import (
    ArchiveRejected, MAGIC, MIN_RETENTION_DAYS, OBJECT_PREFIX,
    _bucket_settings, _get_verified_bytes, _list_valid_versions,
    download_file, main, upload_file,
)

NOW = datetime(2026, 11, 13, 15, 0, tzinfo=timezone.utc)
STATS = {n: {"count": v, "sha256": "a" * 64} for n, v in [
    ("checkpoints", 4), ("checkpoint_pages", 8), ("raw_artifacts", 4)]}
SCHEMA = {"count": 69, "sha256": "b" * 64}
BLOB = _seal(b"PGDMP" + b"\0" * 200, STATS, SCHEMA, b"1" * 32)
SHA = hashlib.sha256(BLOB).hexdigest()
BUCKET = "mar-p0-private-immutable-test"


class Stream(io.BytesIO):
    def close(self):
        super().close()


class Pages:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self, **kwargs):
        yield from self.pages


class FakeS3:
    def __init__(self):
        self.versioning = {"Status": "Enabled"}
        self.lock = {"ObjectLockConfiguration": {
            "ObjectLockEnabled": "Enabled", "Rule": {
                "DefaultRetention": {"Mode": "COMPLIANCE", "Days": 90}}}}
        self.block = {"PublicAccessBlockConfiguration": {
            name: True for name in (
                "BlockPublicAcls", "IgnorePublicAcls",
                "BlockPublicPolicy", "RestrictPublicBuckets")}}
        self.encryption = {"ServerSideEncryptionConfiguration": {
            "Rules": [{"ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"}}]}}
        self.objects = {}
        self.versions = []
        self.last_put = None

    def get_bucket_versioning(self, **kwargs):
        return self.versioning

    def get_object_lock_configuration(self, **kwargs):
        return self.lock

    def get_public_access_block(self, **kwargs):
        return self.block

    def get_bucket_encryption(self, **kwargs):
        return self.encryption

    def put_object(self, **kwargs):
        assert kwargs["IfNoneMatch"] == "*"
        assert kwargs["ChecksumAlgorithm"] == "SHA256"
        assert kwargs["ObjectLockMode"] == "COMPLIANCE"
        assert kwargs["ObjectLockRetainUntilDate"] >= NOW + timedelta(days=90)
        self.last_put = kwargs
        self.objects[(kwargs["Key"], "valid_version_123")] = {
            "payload": kwargs["Body"],
            "sha": kwargs["Metadata"]["ciphertext-sha256"],
            "retention": kwargs["ObjectLockRetainUntilDate"],
            "modified": NOW,
        }
        return {"VersionId": "valid_version_123"}

    def get_paginator(self, operation):
        assert operation == "list_object_versions"
        return Pages([{"Versions": self.versions}])

    def head_object(self, **kwargs):
        item = self.objects[(kwargs["Key"], kwargs["VersionId"])]
        return {
            "VersionId": kwargs["VersionId"], "ObjectLockMode": "COMPLIANCE",
            "ObjectLockRetainUntilDate": item["retention"],
            "ContentLength": len(item["payload"]),
            "Metadata": {"ciphertext-sha256": item["sha"]},
        }

    def get_object(self, **kwargs):
        item = self.objects[(kwargs["Key"], kwargs["VersionId"])]
        return {"Body": Stream(item["payload"])}


class ImmutableArchiveTests(unittest.TestCase):
    def setUp(self):
        self.s3 = FakeS3()

    def test_dry_run_does_not_touch_aws_or_disk(self):
        with patch("scripts.mar_p0_offsite_s3._client_and_bucket") as acquire:
            self.assertEqual(main(["upload", "--encrypted-file", "/unused/x"]), 0)
            acquire.assert_not_called()

    def test_bucket_requires_versioning(self):
        self.s3.versioning = {"Status": "Suspended"}
        with self.assertRaises(ArchiveRejected):
            _bucket_settings(self.s3, BUCKET)

    def test_bucket_requires_compliance_90_days(self):
        for policy in [("GOVERNANCE", 90), ("COMPLIANCE", 30),
                       ("COMPLIANCE", 89), ("COMPLIANCE", "90")]:
            with self.subTest(policy=policy):
                self.s3.lock["ObjectLockConfiguration"]["Rule"]["DefaultRetention"] = {
                    "Mode": policy[0], "Days": policy[1]}
                with self.assertRaises(ArchiveRejected):
                    _bucket_settings(self.s3, BUCKET)

    def test_bucket_rejects_public_access_configuration(self):
        for flag in self.s3.block["PublicAccessBlockConfiguration"]:
            with self.subTest(flag=flag):
                self.s3.block["PublicAccessBlockConfiguration"][flag] = False
                with self.assertRaises(ArchiveRejected):
                    _bucket_settings(self.s3, BUCKET)
                self.s3.block["PublicAccessBlockConfiguration"][flag] = True

    def test_bucket_requires_default_encryption(self):
        self.s3.encryption = {"ServerSideEncryptionConfiguration": {"Rules": []}}
        with self.assertRaises(ArchiveRejected):
            _bucket_settings(self.s3, BUCKET)

    def _upload(self, directory):
        source = Path(directory) / "proof.pgcustom.aesgcm"
        source.write_bytes(BLOB)
        info = upload_file(self.s3, BUCKET, source, SHA, "43295473787", "1", NOW)
        return source, info

    def test_upload_seals_only_encrypted_bytes_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            source, result = self._upload(root)
            self.assertEqual(result["status"], "ciphertext_archived")
            self.assertEqual(result["version_id"], "valid_version_123")
            self.assertEqual(self.s3.last_put["Body"], BLOB)
            self.assertEqual(self.s3.last_put["Metadata"]["ciphertext-sha256"], SHA)
            self.assertEqual(self.s3.last_put["ObjectLockMode"], "COMPLIANCE")
            self.assertEqual(result["retention_days_min"], MIN_RETENTION_DAYS)

    def test_bad_payload_or_wrong_digest_rejected_before_s3_write(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            source = Path(root) / "bad.pgcustom.aesgcm"
            for payload, expected in [(b"PGDMP" + b"0" * 1000, SHA),
                                      (BLOB, "a" * 64),
                                      (BLOB[:18], SHA)]:
                with self.subTest(payload=payload[:5]):
                    source.write_bytes(payload)
                    with self.assertRaises(ArchiveRejected):
                        upload_file(self.s3, BUCKET, source, expected, "123", "1", NOW)
                    self.assertIsNone(self.s3.last_put)

    def test_download_fails_on_wrong_pin_before_output(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            _, obj = self._upload(root)
            destination = Path(root) / "download.enc"
            with self.assertRaises(ArchiveRejected):
                download_file(self.s3, BUCKET, destination, NOW,
                              key=obj["key"], version_id=obj["version_id"],
                              expected_sha="f" * 64)
            self.assertFalse(destination.exists())

    def test_download_requires_live_retention(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            _, obj = self._upload(root)
            self.s3.objects[(obj["key"], obj["version_id"])]["retention"] = NOW
            with self.assertRaises(ArchiveRejected):
                download_file(self.s3, BUCKET, Path(root) / "new", NOW,
                              key=obj["key"], version_id=obj["version_id"])

    def test_download_round_trip_preserves_ciphertext_and_sha(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            _, obj = self._upload(root)
            output = Path(root) / "download.enc"
            check = download_file(self.s3, BUCKET, output, NOW,
                                  key=obj["key"], version_id=obj["version_id"],
                                  expected_sha=SHA)
            self.assertEqual(check["status"], "ciphertext_download_verified")
            self.assertEqual(output.read_bytes(), BLOB)
            self.assertEqual(check["sha256"], SHA)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(ArchiveRejected):
                download_file(self.s3, BUCKET, output, NOW,
                              key=obj["key"], version_id=obj["version_id"])

    def test_latest_version_selection_obeys_age_window(self):
        with tempfile.TemporaryDirectory() as root:
            from os import chmod
            chmod(root, 0o700)
            _, obj = self._upload(root)
            name = obj["key"]
            self.s3.versions = [
                {"Key": name, "VersionId": obj["version_id"],
                 "LastModified": NOW - timedelta(hours=40)},
                {"Key": "some/other/key", "VersionId": "evil",
                 "LastModified": NOW - timedelta(hours=36)},
                {"Key": OBJECT_PREFIX + "too-old.pgcustom.aesgcm",
                 "VersionId": "old",
                 "LastModified": NOW - timedelta(days=35)},
            ]
            self.assertEqual(
                _list_valid_versions(self.s3, BUCKET, NOW, 24, 192),
                (name, obj["version_id"]),
            )
            selected = download_file(self.s3, BUCKET, Path(root) / "selected", NOW,
                                     min_age_h=24, max_age_h=192)
            self.assertEqual(selected["sha256"], SHA)
            with self.assertRaises(ArchiveRejected):
                _list_valid_versions(self.s3, BUCKET, NOW, 48, 192)

    def test_missing_versions_fail_closed(self):
        with self.assertRaises(ArchiveRejected):
            _list_valid_versions(self.s3, BUCKET, NOW, 24, 192)

    def test_invalid_locator_rejected_before_s3_get(self):
        with self.assertRaises(ArchiveRejected):
            _get_verified_bytes(self.s3, BUCKET,
                                "../../secrets", "valid_version_123", SHA, NOW)

    def test_live_cloud_not_contacted_by_offline_tests(self):
        with patch("scripts.mar_p0_offsite_s3._client_and_bucket") as acquire:
            result = main(["download", "--encrypted-file", "/test/output.enc"],
                          {"MAR_P0_S3_BUCKET": BUCKET})
            self.assertEqual(result, 0)
            acquire.assert_not_called()


if __name__ == "__main__":
    unittest.main()
