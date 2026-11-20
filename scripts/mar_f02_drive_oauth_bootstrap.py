#!/usr/bin/env python3
"""Operator-local F02 OAuth setup for a PERSONAL Google Drive; no unattended login.

Default is a dry run. The OAuth consent opens on the operator's own computer.
Credentials are written ONCE to an existing private directory outside git;
the resulting file must never be placed in Drive, GitHub or a chat message.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys

from scripts.mar_p0_offsite_google_drive import (
    DriveBackupRejected, FOLDER_MIME, SCOPE, check_id, verify_folder,
    verify_oauth_scopes,
)
from scripts.mar_p0_offsite_pg_restore import _write_exclusive

ROOT = Path(__file__).resolve().parents[1]


def check_private_file(path: Path) -> None:
    source = path.resolve(strict=True)
    if source.is_relative_to(ROOT):
        raise DriveBackupRejected("oauth_client_json_inside_git_project")
    if path.is_symlink() or not path.is_file():
        raise DriveBackupRejected("oauth_client_json_invalid")
    if os.name == "posix" and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise DriveBackupRejected("oauth_client_json_permissions_not_private")


def check_output_file(path: Path) -> None:
    target = path.resolve(strict=False)
    if target.is_relative_to(ROOT):
        raise DriveBackupRejected("oauth_output_inside_git_project")
    if path.exists() or path.is_symlink():
        raise DriveBackupRejected("no_overwrite_allowed")
    if not path.parent.is_dir():
        raise DriveBackupRejected("private_output_directory_missing")
    if os.name == "posix" and stat.S_IMODE(path.parent.stat().st_mode) & 0o077:
        raise DriveBackupRejected("private_output_directory_not_0700")


def authorize(*, client_json: Path, output: Path, folder_id: str | None, create_folder: bool) -> dict:
    check_private_file(client_json)
    check_output_file(output)
    if create_folder and folder_id:
        raise DriveBackupRejected("choose_existing_or_create_folder")
    if not create_folder:
        check_id(folder_id)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build

        # The client must be 'Desktop app' so localhost OAuth is eligible.
        contents = json.loads(client_json.read_text(encoding="utf-8"))
        if not isinstance(contents, dict) or set(contents) != {"installed"}:
            raise DriveBackupRejected("desktop_oauth_client_required")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_json), scopes=[SCOPE])
        creds = flow.run_local_server(
            host="127.0.0.1", port=0, open_browser=True,
            access_type="offline", prompt="consent",
        )
        verify_oauth_scopes(creds)
        if (not creds.refresh_token or not creds.client_id or not creds.client_secret):
            raise DriveBackupRejected("refresh_token_not_provisioned")
        service = build("drive", "v3", credentials=creds, cache_discovery=False)
        if create_folder:
            created = service.files().create(
                body={"name": "MAR - Backup Neon Criptografado (app)", "mimeType": FOLDER_MIME},
                fields="id",
            ).execute()
            folder_id = check_id(created.get("id") if isinstance(created, dict) else None)
        verify_folder(service, folder_id)
        # Secrets intentionally stay on this computer until operator installs
        # them into protected GitHub Actions environments, never stdout.
        secrets = {
            "MAR_P0_DRIVE_OAUTH_CLIENT_ID": creds.client_id,
            "MAR_P0_DRIVE_OAUTH_CLIENT_SECRET": creds.client_secret,
            "MAR_P0_DRIVE_OAUTH_REFRESH_TOKEN": creds.refresh_token,
            "MAR_P0_GOOGLE_DRIVE_FOLDER_ID": folder_id,
        }
        _write_exclusive(output, (json.dumps(secrets, sort_keys=True) + "\n").encode("utf-8"))
        return {
            "status": "private_oauth_material_created",
            "credentials_printed": False, "private_folder_verified": True,
            "write_mode": "exclusive_0600", "production_gate": "HOLD",
        }
    except DriveBackupRejected:
        raise
    except Exception:
        # Provider errors may include data from the account or OAuth.
        raise DriveBackupRejected("oauth_authorization_or_folder_check_failed") from None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Local F02 Google Drive OAuth setup; default dry-run")
    p.add_argument("--client-json", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--create-app-folder", action="store_true")
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)
    if not args.execute:
        print(json.dumps({"status": "dry_run", "oauth_requests": 0,
                          "file_writes": 0, "production_gate": "HOLD"}))
        return 0
    try:
        report = authorize(
            client_json=args.client_json, output=args.output,
            folder_id=os.environ.get("MAR_P0_GOOGLE_DRIVE_FOLDER_ID"),
            create_folder=args.create_app_folder,
        )
    except (DriveBackupRejected, OSError, ValueError):
        print(json.dumps({"status": "HOLD", "production_gate": "HOLD"}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
