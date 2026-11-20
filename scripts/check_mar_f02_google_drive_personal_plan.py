#!/usr/bin/env python3
"""Validate F02's dated Google Drive personal-backup decision without side effects.

A folder being private and real is NOT evidence of a 90-day WORM backup or
of an active Neon export/restore pipeline. This offline gate must fail closed
on false deployment or retention claims.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/engineering/mar-f02-google-drive-personal-backup-decision.json"

EXPECTED_FALSE = {
    "destination": (
        "folder_id_or_url_in_public_repository",
        "connection_to_github_actions_established",
        "folder_granted_to_backup_oauth_client",
        "oauth_picker_authorization_completed",
        "drive_storage_remaining_measured",
    ),
    "source": ("production_modified", "reader_secret_installed_in_protected_ci"),
    "security": (
        "drive_token_or_key_in_repository",
        "drive_token_or_key_in_drive",
        "encrypted_backup_uploaded",
        "upload_sha256_verified",
        "isolated_restore_on_new_runner",
        "old_backup_restore_tested",
    ),
    "retention": (
        "immutable_WORM_supported_by_selected_destination",
        "immutability_proven",
        "retention_90_days_verified",
        "automatic_deletion_enabled",
    ),
    "activation": (
        "automatic_backup_enabled",
        "scheduled_workflow_deployed",
        "automation_secret_configured",
        "stage_F02_closed",
        "stage_F03_open",
        "public_access_authorized",
    ),
}

EXPECTED_TRUE = {
    "destination": (
        "same_account_as_engineering_memory",
        "private_folder_verified",
        "folder_owner_only",
        "folder_created",
    ),
    "source": ("reader_proven_in_isolated_lab", "reader_provisioned_in_source_branch", "live_reader_preflight_passed"),
    "retention": ("owner_risk_waiver_for_missing_WORM",),
    "security": (
        "authenticated_backup_envelope_required",
        "external_encryption_key_only",
        "scope_to_mar_p0_only",
    ),
}


def validate(doc: object) -> list[str]:
    if not isinstance(doc, dict):
        return ["invalid_root"]
    problems: list[str] = []
    literals = {
        "schema": "mar.f02.google-drive-personal-backup-decision.v1",
        "date": "2026-11-19",
        "stage": "F02",
        "decision": "owner_selected_personal_drive_as_encrypted_offsite_destination",
        "status": "HOLD_NOT_DEPLOYED",
    }
    for key, expected in literals.items():
        if doc.get(key) != expected:
            problems.append(f"incorrect_{key}")
    for section, fields in EXPECTED_FALSE.items():
        node = doc.get(section)
        if not isinstance(node, dict):
            problems.append(f"missing_section_{section}")
            continue
        for key in fields:
            if node.get(key) is not False:
                problems.append(f"{section}.{key}_must_be_false")
    for section, fields in EXPECTED_TRUE.items():
        node = doc.get(section)
        if not isinstance(node, dict):
            if f"missing_section_{section}" not in problems:
                problems.append(f"missing_section_{section}")
            continue
        for key in fields:
            if node.get(key) is not True:
                problems.append(f"{section}.{key}_must_be_true")
    destination = doc.get("destination")
    if isinstance(destination, dict):
        targets = {
            "provider": "google_drive_personal",
            "folder_id_env_name": "MAR_P0_GOOGLE_DRIVE_FOLDER_ID",
            "oauth_scope_target": "https://www.googleapis.com/auth/drive.file",
        }
        for key, expected in targets.items():
            if destination.get(key) != expected:
                problems.append(f"incorrect_destination_{key}")
        # No personal Google Drive folder IDs or OAuth tokens in a public repo:
        if any("folder_id" in key or "oauth_token" in key for key in destination
               if key not in {"folder_id_env_name", "folder_id_or_url_in_public_repository"}):
            problems.append("unapproved_private_folder_metadata")
    source = doc.get("source")
    if isinstance(source, dict):
        expected_source = {
            "provider": "neon_postgresql",
            "project_id": "holy-bread-70461948",
            "branch_intent": "validation_only",
            "dedicated_login": "mar_p0_backup_reader",
        }
        for key, expected in expected_source.items():
            if source.get(key) != expected:
                problems.append(f"incorrect_source_{key}")
        if type(source.get("live_reader_preflight_checks")) is not int or source.get("live_reader_preflight_checks") != 21:
            problems.append("source_read_only_catalog_proof_missing")
    security = doc.get("security")
    if isinstance(security, dict):
        if security.get("encryption_before_upload") != "AES-256-GCM":
            problems.append("encryption_pre_upload_required")
    retention = doc.get("retention")
    if isinstance(retention, dict):
        days = retention.get("operational_target_days")
        if type(days) is not int or days != 90:
            problems.append("retention_target_not_90_days")
    if isinstance(retention, dict):
        acceptance = retention.get("owner_risk_acceptance")
        if not isinstance(acceptance, dict):
            problems.append("owner_risk_acceptance_record_missing")
        else:
            required = {
                "date": "2026-11-19",
                "decision": "explicitly_accepted",
                "scope": "preliminary_development_only",
                "destination": "google_drive_personal_only",
                "risk": "unauthorized_or_accidental_deletion_and_loss_of_recoverable_backups_without_WORM",
            }
            for key, value in required.items():
                if acceptance.get(key) != value:
                    problems.append(f"incorrect_owner_risk_acceptance_{key}")
            expected_controls = {
                "ciphertext_only_AES_256_GCM", "authenticated_readback_sha256",
                "no_automatic_deletion", "operational_target_90_days",
                "independent_restore_required",
            }
            expected_not_proven = {
                "provider_WORM", "backup_uploaded", "successful_restore", "90_days_observed",
            }
            expected_not_authorized = {
                "production_migration", "publication", "cron_activation",
                "stage_F02_closure", "stage_F03_open",
            }
            for key, required_items in (
                ("controls", expected_controls),
                ("does_not_prove", expected_not_proven),
                ("does_not_authorize", expected_not_authorized),
            ):
                value = acceptance.get(key)
                if (not isinstance(value, list) or len(value) != len(required_items)
                        or any(type(item) is not str for item in value)
                        or set(value) != required_items):
                    problems.append(f"incorrect_owner_risk_acceptance_{key}")
    activation = doc.get("activation")
    if isinstance(activation, dict):
        if activation.get("authorization_variable") != "MAR_P0_GOOGLE_DRIVE_BACKUP_ENABLED":
            problems.append("opt_in_gate_missing")
    notices = doc.get("notices")
    if not isinstance(notices, list) or len(notices) < 4 or any(
        not isinstance(x, str) or not x.strip() for x in notices
    ):
        problems.append("risk_disclosures_missing")
    return problems


def main() -> int:
    try:
        doc = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("MAR-F02: FAIL — decision file missing or invalid", file=sys.stderr)
        return 1
    issues = validate(doc)
    if issues:
        for issue in issues:
            print("MAR-F02: HOLD — " + issue, file=sys.stderr)
        return 1
    print("MAR-F02: PASS — scoped Drive non-WORM risk accepted, operational status remains HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
