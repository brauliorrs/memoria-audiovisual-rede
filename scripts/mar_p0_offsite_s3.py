"""Fail-closed S3 archive for MAR P0 already-encrypted PostgreSQL backups.

Only ciphertext produced by mar_p0_offsite_pg_restore.py is transferred.
No S3 key material, Neon credentials or plaintext are accepted by this module.
AWS credentials must come from the workflow's own short-lived OIDC role.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re

OBJECT_PREFIX = "mar-p0/validation/"
MIN_RETENTION_DAYS = 90
MAX_ENCRYPTED_BYTES = 65 * 1024 * 1024
MAGIC = b"MAR-P0-NEON-PGDUMP-AESGCM-V1\0"
HEX_SHA = re.compile(r"[0-9a-f]{64}\Z")
BUCKET_NAME = re.compile(r"[a-z0-9][a-z0-9.-]{2,61}[a-z0-9]\Z")
VERSION_NAME = re.compile(r"[A-Za-z0-9_.=+/\-]{1,1024}\Z")
RUN_ID = re.compile(r"[1-9][0-9]{1,19}\Z")


class ArchiveRejected(ValueError):
    """Stable public error class; do not include sensitive cloud payloads."""


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _iso(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ArchiveRejected("invalid_retention_timestamp")
    return value.astimezone(timezone.utc)


def _bucket_settings(client, bucket):
    """Refuse archival without private, versioned, immutable >=90d storage."""
    version = client.get_bucket_versioning(Bucket=bucket)
    if version.get("Status") != "Enabled":
        raise ArchiveRejected("s3_versioning_disabled")
    config = client.get_object_lock_configuration(Bucket=bucket)
    lock = config.get("ObjectLockConfiguration", {})
    rule = lock.get("Rule", {}).get("DefaultRetention", {})
    if (lock.get("ObjectLockEnabled") != "Enabled"
            or rule.get("Mode") != "COMPLIANCE"
            or type(rule.get("Days")) is not int
            or rule["Days"] < MIN_RETENTION_DAYS):
        raise ArchiveRejected("s3_object_lock_compliance_90d_required")
    block = client.get_public_access_block(Bucket=bucket)
    flags = block.get("PublicAccessBlockConfiguration", {})
    if not all(flags.get(x) is True for x in (
            "BlockPublicAcls", "IgnorePublicAcls",
            "BlockPublicPolicy", "RestrictPublicBuckets")):
        raise ArchiveRejected("s3_public_access_not_fully_blocked")
    encryption = client.get_bucket_encryption(Bucket=bucket)
    rules = encryption.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
    if not any(x.get("ApplyServerSideEncryptionByDefault", {}).get("SSEAlgorithm")
               in ("AES256", "aws:kms") for x in rules):
        raise ArchiveRejected("s3_default_encryption_missing")


def _client_and_bucket(env):
    name = env.get("MAR_P0_S3_BUCKET", "")
    region = env.get("MAR_P0_S3_REGION", "")
    if not BUCKET_NAME.fullmatch(name) or ".." in name or name.startswith("xn--"):
        raise ArchiveRejected("invalid_private_bucket_name")
    if not re.fullmatch(r"[a-z]{2}-[a-z]+-[1-9][0-9]*", region):
        raise ArchiveRejected("invalid_s3_region")
    import boto3  # only used for real, explicitly authorized S3 operations
    return boto3.client("s3", region_name=region), name


def _assert_ciphertext(data, expected):
    if not HEX_SHA.fullmatch(expected or ""):
        raise ArchiveRejected("ciphertext_sha256_required")
    if not MAGIC == data[:len(MAGIC)]:
        raise ArchiveRejected("only_mar_p0_encrypted_payloads_allowed")
    if not 100 < len(data) <= MAX_ENCRYPTED_BYTES:
        raise ArchiveRejected("invalid_ciphertext_size")
    if _digest(data) != expected:
        raise ArchiveRejected("ciphertext_sha256_mismatch")


def _private_directory(path):
    if path.is_symlink() or not path.parent.is_dir():
        raise ArchiveRejected("private_path_required")
    if os.name == "posix" and path.parent.stat().st_mode & 0o077:
        raise ArchiveRejected("private_directory_0700_required")


def upload_file(client, bucket, source, expected_sha, run_id, attempt, now):
    _bucket_settings(client, bucket)
    if not RUN_ID.fullmatch(run_id) or not re.fullmatch(r"[1-9][0-9]{0,2}", attempt):
        raise ArchiveRejected("invalid_run_identifier")
    _private_directory(source)
    if source.is_symlink() or not source.is_file():
        raise ArchiveRejected("encrypted_backup_missing")
    data = source.read_bytes()
    _assert_ciphertext(data, expected_sha)
    dt = _iso(now)
    key = f"{OBJECT_PREFIX}{dt:%Y/%m/%d}/run-{run_id}-a{attempt}.pgcustom.aesgcm"
    digest_b64 = base64.b64encode(hashlib.sha256(data).digest()).decode("ascii")
    response = client.put_object(
        Bucket=bucket, Key=key, Body=data,
        IfNoneMatch="*",  # never overwrite even if a run is replayed
        ContentType="application/octet-stream",
        ChecksumAlgorithm="SHA256",
        ChecksumSHA256=digest_b64,
        Metadata={"ciphertext-sha256": expected_sha, "schema": "mar-p0"},
        ObjectLockMode="COMPLIANCE",
        ObjectLockRetainUntilDate=dt + timedelta(days=MIN_RETENTION_DAYS, minutes=5),
    )
    version = response.get("VersionId", "")
    if not version or not VERSION_NAME.fullmatch(version):
        raise ArchiveRejected("s3_version_id_missing")
    return {"status": "ciphertext_archived", "key": key, "version_id": version,
            "sha256": expected_sha, "retention_days_min": MIN_RETENTION_DAYS,
            "production_gate": "HOLD"}


def _list_valid_versions(client, bucket, now, min_age_h, max_age_h):
    if not (0 <= min_age_h <= max_age_h <= 24 * 90):
        raise ArchiveRejected("invalid_recovery_age_window")
    upper = _iso(now) - timedelta(hours=min_age_h)
    lower = _iso(now) - timedelta(hours=max_age_h)
    paginator = client.get_paginator("list_object_versions")
    matching = []
    for page in paginator.paginate(Bucket=bucket, Prefix=OBJECT_PREFIX):
        for version in page.get("Versions", []):
            name = version.get("Key", "")
            modified = version.get("LastModified")
            if (isinstance(modified, datetime) and modified.tzinfo is not None
                    and lower <= _iso(modified) <= upper
                    and name.startswith(OBJECT_PREFIX)
                    and name.endswith(".pgcustom.aesgcm")
                    and VERSION_NAME.fullmatch(str(version.get("VersionId", "")))
                    and not version.get("IsDeleteMarker", False)):
                matching.append((_iso(modified), name, version["VersionId"]))
    if not matching:
        raise ArchiveRejected("no_backup_in_required_recovery_window")
    _, key, version_id = sorted(matching, reverse=True)[0]
    return key, version_id


def _get_verified_bytes(client, bucket, key, version_id, expected_sha, now):
    if (not key.startswith(OBJECT_PREFIX) or not re.fullmatch(
            r"mar-p0/validation/[0-9]{4}/[0-9]{2}/[0-9]{2}/run-[0-9]+-a[0-9]+\.pgcustom\.aesgcm",
            key) or not VERSION_NAME.fullmatch(version_id or "")):
        raise ArchiveRejected("invalid_backup_locator")
    head = client.head_object(Bucket=bucket, Key=key, VersionId=version_id)
    if (head.get("VersionId") != version_id
            or head.get("ObjectLockMode") != "COMPLIANCE"
            or _iso(head.get("ObjectLockRetainUntilDate")) <
               _iso(now) + timedelta(days=1)
            or head.get("ContentLength", 0) > MAX_ENCRYPTED_BYTES):
        raise ArchiveRejected("archive_version_not_protected")
    metadata_sha = head.get("Metadata", {}).get("ciphertext-sha256", "")
    if not HEX_SHA.fullmatch(metadata_sha):
        raise ArchiveRejected("archive_sha256_metadata_missing")
    if expected_sha and metadata_sha != expected_sha:
        raise ArchiveRejected("independent_sha256_mismatch")
    answer = client.get_object(Bucket=bucket, Key=key, VersionId=version_id)
    try:
        data = answer["Body"].read(MAX_ENCRYPTED_BYTES + 1)
    finally:
        answer["Body"].close()
    _assert_ciphertext(data, metadata_sha)
    return data, metadata_sha


def download_file(client, bucket, destination, now, *,
                  key=None, version_id=None, expected_sha=None,
                  min_age_h=0, max_age_h=192):
    _bucket_settings(client, bucket)
    if (key is None) != (version_id is None):
        raise ArchiveRejected("incomplete_object_version_pin")
    if key is None:
        key, version_id = _list_valid_versions(client, bucket, now, min_age_h, max_age_h)
    _private_directory(destination)
    if destination.exists() or destination.is_symlink():
        raise ArchiveRejected("restore_download_target_must_be_new")
    data, sha = _get_verified_bytes(client, bucket, key, version_id,
                                    expected_sha, now)
    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {"status": "ciphertext_download_verified",
            "key": key, "version_id": version_id, "sha256": sha,
            "production_gate": "HOLD"}


def main(argv=None, environ=None, *, client=None, clock=None):
    parser = argparse.ArgumentParser(description="MAR P0 immutable S3 ciphertext archive")
    parser.add_argument("action", choices=("upload", "download"))
    parser.add_argument("--encrypted-file", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--key")
    parser.add_argument("--version-id")
    parser.add_argument("--run-id")
    parser.add_argument("--attempt", default="1")
    parser.add_argument("--min-age-hours", type=int, default=0)
    parser.add_argument("--max-age-hours", type=int, default=192)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "aws_requests": 0,
                          "filesystem_writes": 0, "production_gate": "HOLD"}))
        return 0
    env = os.environ if environ is None else environ
    try:
        if client is None:
            client, bucket = _client_and_bucket(env)
        else:
            bucket = env.get("MAR_P0_S3_BUCKET", "synthetic-only")
        now = datetime.now(timezone.utc) if clock is None else clock
        if args.action == "upload":
            if not args.run_id:
                raise ArchiveRejected("run_id_required")
            result = upload_file(client, bucket, args.encrypted_file,
                                 args.expected_sha256, args.run_id,
                                 args.attempt, now)
        else:
            result = download_file(client, bucket, args.encrypted_file, now,
                                   key=args.key, version_id=args.version_id,
                                   expected_sha=args.expected_sha256,
                                   min_age_h=args.min_age_hours,
                                   max_age_h=args.max_age_hours)
    except (ArchiveRejected, OSError, KeyError, ValueError, TypeError):
        print(json.dumps({"status": "HOLD", "production_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
