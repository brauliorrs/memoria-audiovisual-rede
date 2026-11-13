"""Vercel *private* Blob transport for authenticated MAR P0 ciphertext only.

Not WORM: Vercel Blob has no verified S3 Object Lock equivalent. A 90-day
minimum is a *policy*, not provider-enforced protection against deletion.
External GitHub runners require a BLOB_READ_WRITE_TOKEN, which can also delete.
No Neon credentials or plaintext are sent to Vercel. No delete API is used.
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
SHA = re.compile(r"[a-f0-9]{64}\Z")
RUN = re.compile(r"[1-9][0-9]{1,19}\Z")
LOCATION = re.compile(
    r"mar-p0/validation/[0-9]{4}/[0-9]{2}/[0-9]{2}/"
    r"run-[0-9]+-a[0-9]+-sha256-([0-9a-f]{64})\.pgcustom\.aesgcm\Z"
)


class BackupRejected(ValueError):
    """Fail closed, no secrets or payloads in user-facing error messages."""


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


def token_from(env):
    token = env.get("MAR_P0_VERCEL_BLOB_READ_WRITE_TOKEN", "")
    if not isinstance(token, str) or not token.strip() or len(token) < 20:
        raise BackupRejected("private_vercel_blob_token_required")
    return token


def _uploaded_at(item):
    dt = item.uploaded_at
    if not isinstance(dt, datetime) or dt.tzinfo is None:
        raise BackupRejected("blob_timestamp_invalid")
    return dt.astimezone(timezone.utc)


def choose_older_blob(list_pages, *, now, min_hours=24, max_hours=192):
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise BackupRejected("utc_clock_required")
    if not 0 <= min_hours <= max_hours <= 24 * 90:
        raise BackupRejected("recovery_window_invalid")
    now = now.astimezone(timezone.utc)
    matches = []
    for item in list_pages:
        match = LOCATION.fullmatch(item.pathname)
        if not match:
            continue
        dt = _uploaded_at(item)
        if now - timedelta(hours=max_hours) <= dt <= now - timedelta(hours=min_hours):
            matches.append((dt, item.pathname, match.group(1)))
    if not matches:
        raise BackupRejected("older_private_backup_not_found")
    _, pathname, sha = max(matches, key=lambda v: (v[0], v[1]))
    return pathname, sha


async def read_from_private_blob(client, pathname, token):
    match = LOCATION.fullmatch(pathname or "")
    if not match:
        raise BackupRejected("invalid_private_blob_path")
    result = await client.get(pathname, access="private", token=token)
    if result is None or result.status_code != 200 or result.stream is None:
        raise BackupRejected("private_blob_missing")
    if result.blob.pathname != pathname:
        raise BackupRejected("blob_path_changed")
    output = bytearray()
    async for chunk in result.stream:
        if not isinstance(chunk, (bytes, bytearray)):
            raise BackupRejected("invalid_blob_stream")
        output.extend(chunk)
        if len(output) > MAX_BYTES:
            raise BackupRejected("ciphertext_exceeds_safety_limit")
    data = bytes(output)
    assert_cipher(data, match.group(1))
    return data, match.group(1)


async def put_private(client, source, expected, run_id, attempt, token, *, now):
    assert_private_file(source, exists=True)
    if not RUN.fullmatch(str(run_id)) or not re.fullmatch(r"[1-9][0-9]{0,3}", str(attempt)):
        raise BackupRejected("run_identifier_invalid")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise BackupRejected("utc_clock_required")
    data = source.read_bytes()
    assert_cipher(data, expected)
    date = now.astimezone(timezone.utc)
    path = (f"{PREFIX}{date:%Y/%m/%d}/run-{run_id}-a{attempt}-"
            f"sha256-{expected}.pgcustom.aesgcm")
    uploaded = await client.put(
        path, data, access="private", content_type="application/octet-stream",
        add_random_suffix=False, overwrite=False, token=token,
    )
    if uploaded.pathname != path or ".private.blob.vercel-storage.com/" not in uploaded.url:
        raise BackupRejected("private_blob_upload_not_confirmed")
    # Read back through authenticated route; no success based on upload alone.
    remote, sha = await read_from_private_blob(client, path, token)
    if sha != expected or remote != data:
        raise BackupRejected("private_blob_readback_mismatch")
    return {"status": "private_ciphertext_uploaded_and_readback_verified",
            "pathname": path, "sha256": sha,
            "provider_retention_enforced": False,
            "production_gate": "HOLD"}


async def fetch_private(client, dest, token, *, pathname, expected):
    assert_private_file(dest, exists=False)
    if not LOCATION.fullmatch(pathname or ""):
        raise BackupRejected("invalid_private_blob_path")
    if expected and (not SHA.fullmatch(expected) or
                     expected != LOCATION.fullmatch(pathname).group(1)):
        raise BackupRejected("independent_sha256_mismatch")
    data, sha = await read_from_private_blob(client, pathname, token)
    fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return {"status": "private_ciphertext_download_verified",
            "pathname": pathname, "sha256": sha,
            "production_gate": "HOLD"}


async def list_old_blobs(token, *, now, min_hours, max_hours):
    from vercel.blob import list_objects
    import asyncio
    cursor = None
    items = []
    # The Python SDK provides synchronous list_objects. Run it off the event loop.
    for _ in range(100):
        kwargs = {"prefix": PREFIX, "limit": 1000, "token": token}
        if cursor:
            kwargs["cursor"] = cursor
        page = await asyncio.to_thread(list_objects, **kwargs)
        items.extend(page.blobs)
        if not page.has_more:
            return choose_older_blob(items, now=now, min_hours=min_hours,
                                     max_hours=max_hours)
        if not page.cursor or page.cursor == cursor:
            raise BackupRejected("blob_pagination_invalid")
        cursor = page.cursor
    raise BackupRejected("blob_listing_exceeds_safety_limit")


async def execute(action, args, *, client, token, now):
    if action == "upload":
        if not args.expected_sha256:
            raise BackupRejected("upload_checksum_required")
        return await put_private(client, args.encrypted_file,
                                 args.expected_sha256, args.run_id,
                                 args.attempt, token, now=now)
    if args.pathname:
        pathname = args.pathname
        expected = args.expected_sha256
    else:
        pathname, expected = await list_old_blobs(
            token, now=now, min_hours=args.min_age_hours,
            max_hours=args.max_age_hours)
    return await fetch_private(client, args.encrypted_file, token,
                               pathname=pathname, expected=expected)


def main(argv=None, environ=None, *, client=None, clock=None):
    p = argparse.ArgumentParser(description="MAR P0 private Vercel Blob ciphertext")
    p.add_argument("action", choices=("upload", "download"))
    p.add_argument("--encrypted-file", type=Path, required=True)
    p.add_argument("--expected-sha256")
    p.add_argument("--pathname")
    p.add_argument("--run-id")
    p.add_argument("--attempt", default="1")
    p.add_argument("--min-age-hours", type=int, default=24)
    p.add_argument("--max-age-hours", type=int, default=192)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "network_requests": 0,
                          "filesystem_writes": 0, "production_gate": "HOLD"}))
        return 0
    env = os.environ if environ is None else environ
    try:
        token = token_from(env)
        if client is None:
            from vercel.blob import AsyncBlobClient
            client = AsyncBlobClient()
        now = datetime.now(timezone.utc) if clock is None else clock
        result = asyncio.run(execute(args.action, args, client=client,
                                     token=token, now=now))
    except (BackupRejected, OSError, KeyError, ValueError, TypeError):
        print(json.dumps({"status": "HOLD", "production_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
