#!/usr/bin/env python3
"""F02: Drive-only transport of already-encrypted MAR P0 backups.

Operator-invoked, no schedule and no silent authorization. OAuth credentials
are provided at runtime through protected environment secrets; never logged.
The ChatGPT Drive connector is NOT an OAuth credential for this application.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys

from scripts.mar_p0_offsite_pg_restore import MAGIC, MAX_FILE_BYTES, _write_exclusive

SCOPE = "https://www.googleapis.com/auth/drive.file"
FOLDER_MIME = "application/vnd.google-apps.folder"
FILE_MIME = "application/octet-stream"
ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{15,180}\Z")
SHA_PATTERN = re.compile(r"[a-f0-9]{64}\Z")
NAME_PATTERN = re.compile(
    r"mar-p0-[0-9]{8}T[0-9]{6}Z-run-[0-9]{2,20}-a[0-9]{1,4}-"
    r"sha256-([a-f0-9]{64})\.pgcustom\.aesgcm\Z"
)


class DriveBackupRejected(ValueError):
    """Deliberately generic errors: do not propagate provider or auth details."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def check_cipher(raw: bytes, expected_sha: str) -> None:
    if not SHA_PATTERN.fullmatch(expected_sha or ""):
        raise DriveBackupRejected("sha256_pin_required")
    if not (len(MAGIC) + 48 < len(raw) <= MAX_FILE_BYTES):
        raise DriveBackupRejected("ciphertext_size_invalid")
    if not raw.startswith(MAGIC) or sha256(raw) != expected_sha:
        raise DriveBackupRejected("ciphertext_invalid")


def check_id(value: str) -> str:
    if not isinstance(value, str) or not ID_PATTERN.fullmatch(value):
        raise DriveBackupRejected("drive_id_invalid")
    return value


def check_local(path: Path, *, exists: bool) -> None:
    if path.is_symlink() or not path.parent.is_dir():
        raise DriveBackupRejected("private_directory_missing")
    if os.name == "posix" and path.parent.stat().st_mode & 0o077:
        raise DriveBackupRejected("private_directory_mode_invalid")
    if exists and (not path.is_file() or path.stat().st_size > MAX_FILE_BYTES):
        raise DriveBackupRejected("source_file_unavailable")
    if not exists and path.exists():
        raise DriveBackupRejected("no_overwrite_allowed")


def new_name(expected_sha: str, *, run_id: str, attempt: str, now: datetime) -> str:
    if not SHA_PATTERN.fullmatch(expected_sha or ""):
        raise DriveBackupRejected("sha256_pin_required")
    if not re.fullmatch(r"[0-9]{2,20}", run_id or ""):
        raise DriveBackupRejected("run_id_invalid")
    if not re.fullmatch(r"[1-9][0-9]{0,3}", attempt or ""):
        raise DriveBackupRejected("run_attempt_invalid")
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise DriveBackupRejected("utc_clock_required")
    stamp = now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"mar-p0-{stamp}-run-{run_id}-a{attempt}-sha256-{expected_sha}.pgcustom.aesgcm"


def get_service(env: dict):
    """Obtain OAuth session; forbid silently extending scope to full Drive."""
    keys = (
        "MAR_P0_DRIVE_OAUTH_CLIENT_ID",
        "MAR_P0_DRIVE_OAUTH_CLIENT_SECRET",
        "MAR_P0_DRIVE_OAUTH_REFRESH_TOKEN",
    )
    if any(not isinstance(env.get(key), str) or not env[key].strip() for key in keys):
        raise DriveBackupRejected("oauth_secrets_unavailable")
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        creds = Credentials(
            token=None,
            refresh_token=env[keys[2]],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env[keys[0]],
            client_secret=env[keys[1]],
            scopes=[SCOPE],
        )
        creds.refresh(Request())
        # A configured scope is NOT proof of the scopes actually issued.
        # If Google omits granted_scopes, do not guess authorization.
        if set(creds.granted_scopes or ()) != {SCOPE}:
            raise DriveBackupRejected("oauth_granted_scope_not_exact")
        return build("drive", "v3", credentials=creds, cache_discovery=False)
    except DriveBackupRejected:
        raise
    except Exception:
        # No raw API errors: they can carry identity or account information.
        raise DriveBackupRejected("oauth_session_unavailable") from None


def verify_folder(service, folder_id: str) -> None:
    check_id(folder_id)
    meta = service.files().get(
        fileId=folder_id, fields="id,mimeType,trashed,shared"
    ).execute()
    if (not isinstance(meta, dict) or meta.get("id") != folder_id
            or meta.get("mimeType") != FOLDER_MIME
            or meta.get("trashed") is not False
            or meta.get("shared") is not False):
        raise DriveBackupRejected("private_folder_not_verified")


def verify_file_metadata(service, file_id: str, folder_id: str, name: str, expected_sha: str, expected_size: int) -> None:
    meta = service.files().get(
        fileId=check_id(file_id),
        fields="id,name,mimeType,parents,trashed,size,appProperties"
    ).execute()
    if (not isinstance(meta, dict) or meta.get("id") != file_id
            or meta.get("name") != name or not NAME_PATTERN.fullmatch(name)
            or NAME_PATTERN.fullmatch(name).group(1) != expected_sha
            or meta.get("mimeType") != FILE_MIME
            or meta.get("parents") != [folder_id]
            or meta.get("trashed") is not False
            or meta.get("appProperties", {}).get("sha256") != expected_sha
            or str(meta.get("size")) != str(expected_size)):
        raise DriveBackupRejected("remote_ciphertext_metadata_invalid")


def fetch_cipher(service, file_id: str, folder_id: str, name: str, expected_sha: str, expected_size: int) -> bytes:
    verify_file_metadata(service, file_id, folder_id, name, expected_sha, expected_size)
    raw = service.files().get_media(fileId=file_id).execute()
    if not isinstance(raw, bytes) or len(raw) != expected_size:
        raise DriveBackupRejected("remote_bytes_invalid")
    check_cipher(raw, expected_sha)
    return raw


def upload(service, *, folder_id: str, path: Path, expected_sha: str, run_id: str, attempt: str, now: datetime) -> dict:
    verify_folder(service, folder_id)
    check_local(path, exists=True)
    raw = path.read_bytes()
    check_cipher(raw, expected_sha)
    name = new_name(expected_sha, run_id=run_id, attempt=attempt, now=now)
    from googleapiclient.http import MediaIoBaseUpload
    import io
    media = MediaIoBaseUpload(
        io.BytesIO(raw), mimetype=FILE_MIME, resumable=True, chunksize=8 * 1024 * 1024
    )
    result = service.files().create(
        body={
            "name": name, "parents": [folder_id], "mimeType": FILE_MIME,
            "appProperties": {"sha256": expected_sha, "mar_stage": "F02"}
        },
        media_body=media,
        fields="id",
    ).execute()
    file_id = check_id(result.get("id") if isinstance(result, dict) else None)
    downloaded = fetch_cipher(service, file_id, folder_id, name, expected_sha, len(raw))
    if downloaded != raw:
        raise DriveBackupRejected("remote_readback_mismatch")
    return {
        "file_id": file_id, "file_name": name, "folder_id": folder_id,
        "sha256": expected_sha, "size": len(raw),
        "provider": "google_drive_personal", "verified": True,
        "worm_proven": False, "production_gate": "HOLD",
    }


def download(service, *, receipt: dict, target: Path, folder_id: str) -> dict:
    if not isinstance(receipt, dict) or receipt.get("folder_id") != folder_id:
        raise DriveBackupRejected("receipt_folder_mismatch")
    if receipt.get("provider") != "google_drive_personal" or receipt.get("verified") is not True:
        raise DriveBackupRejected("receipt_not_verified")
    file_id = check_id(receipt.get("file_id"))
    name = receipt.get("file_name")
    expected_sha = receipt.get("sha256")
    expected_size = receipt.get("size")
    if (not isinstance(name, str) or NAME_PATTERN.fullmatch(name) is None
            or not SHA_PATTERN.fullmatch(expected_sha or "")
            or type(expected_size) is not int or expected_size <= 0
            or expected_size > MAX_FILE_BYTES):
        raise DriveBackupRejected("receipt_invalid")
    check_local(target, exists=False)
    verify_folder(service, folder_id)
    raw = fetch_cipher(service, file_id, folder_id, name, expected_sha, expected_size)
    _write_exclusive(target, raw)
    return {"status": "drive_ciphertext_download_verified", "sha256": expected_sha,
            "size": len(raw), "production_gate": "HOLD"}


def main(argv: list[str] | None = None, env=None, *, service=None, now=None) -> int:
    parser = argparse.ArgumentParser(description="F02: Google Drive encrypted transport, never plaintext")
    parser.add_argument("action", choices=("upload", "download"))
    parser.add_argument("--encrypted-file", required=True, type=Path)
    parser.add_argument("--receipt-file", required=True, type=Path)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--run-id")
    parser.add_argument("--attempt", default="1")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "requests": 0, "writes": 0, "production_gate": "HOLD"}))
        return 0
    runtime = os.environ if env is None else env
    try:
        folder_id = check_id(runtime.get("MAR_P0_GOOGLE_DRIVE_FOLDER_ID"))
        client = service if service is not None else get_service(runtime)
        if args.action == "upload":
            check_local(args.receipt_file, exists=False)
            report = upload(
                client, folder_id=folder_id, path=args.encrypted_file,
                expected_sha=args.expected_sha256, run_id=args.run_id,
                attempt=args.attempt, now=now or datetime.now(timezone.utc),
            )
            # The private receipt is required to locate the object later.
            # Do not include the private file/folder ID in stdout or logs.
            _write_exclusive(
                args.receipt_file, (json.dumps(report, sort_keys=True) + "\n").encode("utf-8")
            )
            result = {"status": "drive_ciphertext_uploaded_and_readback_verified",
                      "sha256": report["sha256"], "size": report["size"],
                      "receipt_private": True, "worm_proven": False, "production_gate": "HOLD"}
        else:
            check_local(args.receipt_file, exists=True)
            receipt = json.loads(args.receipt_file.read_text(encoding="utf-8"))
            result = download(client, receipt=receipt, target=args.encrypted_file, folder_id=folder_id)
    except Exception:
        # Deliberately suppress raw provider exceptions and all credentials.
        print(json.dumps({"status": "HOLD", "production_gate": "HOLD"}))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
