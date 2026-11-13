"""Fail-closed PRIVATE Vercel Blob transport for MAR P0 ciphertext only.

Uses the official vercel-blob >= 0.5.1 Python module-level API:
put_blob/get_blob/query_blobs. The SDK reads BLOB_READ_WRITE_TOKEN from
the executor's own secret environment, not the source repository.

Vercel Blob is NOT WORM; a token with write access can also delete backups.
The minimum 90-day retention requirement is not provider-enforced here.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re

MAGIC = b"MAR-P0-NEON-PGDUMP-AESGCM-V1\0"
PREFIX = "mar-p0/validation/"
MAX_BYTES = 65 * 1024 * 1024
MAX_LISTED = 10000
SHA = re.compile(r"[a-f0-9]{64}\Z")
RUN = re.compile(r"[1-9][0-9]{1,19}\Z")
LOCATION = re.compile(
    r"mar-p0/validation/[0-9]{4}/[0-9]{2}/[0-9]{2}/"
    r"run-[0-9]+-a[0-9]+-sha256-([0-9a-f]{64})\.pgcustom\.aesgcm\Z"
)


class BackupRejected(ValueError):
    """Stable fail-closed failure class, no secret-bearing messages."""


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def assert_cipher(blob: bytes, expected: str) -> None:
    if not SHA.fullmatch(expected or ""):
        raise BackupRejected("sha256_required")
    if not 100 < len(blob) <= MAX_BYTES or not blob.startswith(MAGIC):
        raise BackupRejected("invalid_mar_p0_encrypted_envelope")
    if digest(blob) != expected:
        raise BackupRejected("ciphertext_sha256_mismatch")


def assert_private_file(path: Path, *, exists: bool) -> None:
    if path.is_symlink() or not path.parent.is_dir():
        raise BackupRejected("private_directory_required")
    if os.name == "posix" and path.parent.stat().st_mode & 0o077:
        raise BackupRejected("private_directory_0700_required")
    if exists and not path.is_file():
        raise BackupRejected("encrypted_file_missing")
    if not exists and path.exists():
        raise BackupRejected("cannot_overwrite_existing_file")


def check_auth(env) -> None:
    candidate = env.get("BLOB_READ_WRITE_TOKEN", "")
    if not isinstance(candidate, str) or len(candidate.strip()) < 20:
        raise BackupRejected("private_vercel_blob_token_required")


def uploaded_at(item):
    value = item.uploaded_at
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise BackupRejected("blob_timestamp_invalid")
    return value.astimezone(timezone.utc)


def choose_older_blob(items, *, now, min_hours=24, max_hours=192):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise BackupRejected("utc_clock_required")
    if not (0 <= min_hours <= max_hours <= 24 * 90):
        raise BackupRejected("recovery_window_invalid")
    now = now.astimezone(timezone.utc)
    matches = []
    for item in items:
        match = LOCATION.fullmatch(item.pathname)
        if not match:
            continue
        when = uploaded_at(item)
        if now - timedelta(hours=max_hours) <= when <= now - timedelta(hours=min_hours):
            matches.append((when, item.pathname, match.group(1)))
    if not matches:
        raise BackupRejected("older_private_backup_not_found")
    _, pathname, sha = max(matches, key=lambda x: (x[0], x[1]))
    return pathname, sha


async def read_private(client, pathname):
    match = LOCATION.fullmatch(pathname or "")
    if not match:
        raise BackupRejected("invalid_private_blob_path")
    result = await client.get_blob(pathname, access="private")
    if (result is None or result.metadata.status_code != 200
            or not isinstance(result.body, bytes)):
        raise BackupRejected("private_blob_missing")
    data = result.body
    assert_cipher(data, match.group(1))
    return data, match.group(1)


async def upload_private(client, source, expected, run_id, attempt, *, now):
    assert_private_file(source, exists=True)
    if not RUN.fullmatch(str(run_id)) or not re.fullmatch(r"[1-9][0-9]{0,3}", str(attempt)):
        raise BackupRejected("run_identifier_invalid")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise BackupRejected("utc_clock_required")
    data = source.read_bytes()
    assert_cipher(data, expected)
    dt = now.astimezone(timezone.utc)
    pathname = (f"{PREFIX}{dt:%Y/%m/%d}/run-{run_id}-a{attempt}-"
                f"sha256-{expected}.pgcustom.aesgcm")
    uploaded = await client.put_blob(
        pathname, data, access="private",
        content_type="application/octet-stream",
        add_random_suffix=False, allow_overwrite=False,
    )
    if (uploaded.pathname != pathname
            or ".private.blob.vercel-storage.com/" not in uploaded.url):
        raise BackupRejected("private_blob_upload_not_confirmed")
    # SHA readback by authenticated download, not just a server acknowledgment.
    remote, sha = await read_private(client, pathname)
    if remote != data or sha != expected:
        raise BackupRejected("private_blob_readback_mismatch")
    return {"status": "private_ciphertext_uploaded_and_readback_verified",
            "pathname": pathname, "sha256": sha,
            "provider_retention_enforced": False,
            "production_gate": "HOLD"}


async def download_private(client, destination, *, pathname, expected=None):
    assert_private_file(destination, exists=False)
    match = LOCATION.fullmatch(pathname or "")
    if match is None:
        raise BackupRejected("invalid_private_blob_path")
    if expected is not None and (
            not SHA.fullmatch(expected) or expected != match.group(1)):
        raise BackupRejected("independent_sha256_mismatch")
    data, sha = await read_private(client, pathname)
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as writer:
            writer.write(data)
            writer.flush()
            os.fsync(writer.fileno())
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {"status": "private_ciphertext_download_verified",
            "pathname": pathname, "sha256": sha,
            "production_gate": "HOLD"}


async def find_prior(client, *, now, min_age_hours, max_age_hours):
    items = []
    # Official SDK query_blobs follows pagination transparently.
    async for item in client.query_blobs(prefix=PREFIX, page_size=100):
        items.append(item)
        if len(items) > MAX_LISTED:
            raise BackupRejected("too_many_versions_to_audit")
    return choose_older_blob(
        items, now=now, min_hours=min_age_hours, max_hours=max_age_hours
    )


async def execute(action, args, *, client, now):
    if action == "upload":
        return await upload_private(
            client, args.encrypted_file, args.expected_sha256,
            args.run_id, args.attempt, now=now,
        )
    if args.pathname is not None:
        pathname, expected = args.pathname, args.expected_sha256
    else:
        pathname, expected = await find_prior(
            client, now=now, min_age_hours=args.min_age_hours,
            max_age_hours=args.max_age_hours,
        )
    return await download_private(
        client, args.encrypted_file, pathname=pathname, expected=expected
    )


def main(argv=None, environ=None, *, client=None, clock=None):
    parser = argparse.ArgumentParser(description="MAR P0 private Vercel Blob ciphertext")
    parser.add_argument("action", choices=("upload", "download"))
    parser.add_argument("--encrypted-file", type=Path, required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--pathname")
    parser.add_argument("--run-id")
    parser.add_argument("--attempt", default="1")
    parser.add_argument("--min-age-hours", type=int, default=24)
    parser.add_argument("--max-age-hours", type=int, default=192)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "network_requests": 0,
                          "filesystem_writes": 0, "production_gate": "HOLD"}))
        return 0
    env = os.environ if environ is None else environ
    try:
        check_auth(env)
        if client is None:
            from vercel import blob  # pip install vercel-blob==0.5.1
            client = blob
        now = datetime.now(timezone.utc) if clock is None else clock
        result = asyncio.run(execute(args.action, args, client=client, now=now))
    except (BackupRejected, OSError, ValueError, TypeError):
        print(json.dumps({"status": "HOLD", "production_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
