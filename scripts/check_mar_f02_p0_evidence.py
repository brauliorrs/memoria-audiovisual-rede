#!/usr/bin/env python3
"""Offline fail-closed checker for the dated MAR F02 Neon P0 audit record.

This validates evidence consistency, not the current Neon account state.
Never accepts a clone as an independent restore or test-grants as production.
No DB access, credentials, network, secret material, or side effects.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/engineering/mar-f02-p0-neon-evidence-20261119.json"
TABLES = frozenset({"checkpoint_pages", "checkpoints", "raw_artifacts"})
DML = ("insert", "update", "delete")
BASELINE_ROWS = {"checkpoints": 4, "checkpoint_pages": 8, "raw_artifacts": 4}
REQUIRED = frozenset({
    "owner_only_security_review_recorded",
    "production_read_only_role_validated",
    "default_branch_protection_verified",
    "scheduled_backup_and_retention_verified",
    "independent_snapshot_or_encrypted_offsite_restore_verified",
    "secrets_in_ci_verified",
    "rollback_end_to_end_verified",
})


def validate_report(doc: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict):
        return ["F02 evidence must be an object"]
    if doc.get("schema") != "mar.f02.p0.neon-evidence.v1":
        errors.append("unsupported schema")
    if doc.get("stage") != "F02" or doc.get("status") != "HOLD":
        errors.append("dated F02 baseline must remain HOLD (not a completion attestation)")
    if doc.get("observation_date") != "2026-11-19":
        errors.append("observation date altered")
    project = doc.get("project") or {}
    main = doc.get("production") or {}
    original = doc.get("validation_source") or {}
    lab = doc.get("isolated_lab") or {}
    probe = doc.get("snapshot_probe") or {}
    required = doc.get("p0_requirements") or {}
    if not all(isinstance(x, dict) for x in
               (project, main, original, lab, probe, required)):
        return errors + ["nested evidence structure invalid"]
    if (project.get("id") != "holy-bread-70461948"
            or project.get("history_retention_seconds") != 21600
            or project.get("automatic_snapshots_count") != 0
            or project.get("default_branch_snapshot_schedule_count") != 0):
        errors.append("baseline project data changed: re-audit with new dated evidence")
    if (main.get("branch_id") != "br-raspy-river-b8qx9oo9"
            or main.get("default") is not True
            or main.get("protected") is not False
            or main.get("modified") is not False
            or main.get("read_only_role_demonstrated") is not False):
        errors.append("production baseline misrepresented")
    if (original.get("branch_id") != "br-lingering-smoke-b8hjdnzb"
            or original.get("modified") is not False
            or original.get("read_only") is not False):
        errors.append("original validation branch was not readonly and must remain unchanged")
    before = original.get("grants_before")
    after = lab.get("grants_after")
    if not isinstance(before, dict) or set(before) != TABLES:
        errors.append("original three-table grants absent")
    else:
        if not all(isinstance(before[t], dict) for t in TABLES):
            errors.append("original grants must be objects")
        else:
            if not all(before[t].get("select") is True for t in TABLES):
                errors.append("original SELECT capability missing")
            if not (before["checkpoints"].get("update") is True
                    and all(before[t].get("insert") is True for t in TABLES)):
                errors.append("actual DML exposure not disclosed")
    if (lab.get("parent_id") != original.get("branch_id")
            or lab.get("branch_id") != "br-purple-art-b8p4uvdr"
            or lab.get("modified_only_this_branch") is not True
            or lab.get("independent_restore_proven") is not False
            or lab.get("backup_durability_proven") is not False):
        errors.append("lab isolation, restore or backup proof overstated")
    if not isinstance(after, dict) or set(after) != TABLES:
        errors.append("lab's three-table grants absent")
    else:
        for table in TABLES:
            grants = after[table]
            if not isinstance(grants, dict) or grants.get("select") is not True:
                errors.append(f"{table}: SELECT read permission missing")
                continue
            if any(grants.get(privilege) is not False for privilege in DML):
                errors.append(f"{table}: lab reader has write privileges")
    reader = lab.get("dedicated_reader")
    if not isinstance(reader, dict):
        errors.append("dedicated read-only lab role evidence missing")
    else:
        required_reader = {
            "name": "mar_p0_reader",
            "created_in_isolated_lab_only": True,
            "login": False,
            "superuser": False,
            "create_db": False,
            "create_role": False,
            "schema_usage": True,
            "select_on_all_three_tables": True,
            "dml_on_any_three_tables": False,
            "production_login_provisioned": False,
            "production_grants_applied": False,
        }
        if any(reader.get(key) != expected for key, expected in required_reader.items()):
            errors.append("dedicated lab reader privilege or production scope overstated")
    login = lab.get("dedicated_backup_login")
    login_expect = {
        "name": "mar_p0_backup_reader",
        "branch_id": "br-purple-art-b8p4uvdr",
        "scope": "isolated_lab_only",
        "created_with_neon_read_only_access": True,
        "login": True,
        "inherit_roles": False,
        "admin": False,
        "member_of_other_roles": False,
        "database_create": False,
        "schema_create": False,
        "table_owner": False,
        "any_table_or_column_dml": False,
        "executable_security_definer_in_mar_p0": False,
        "table_count": 3,
        "select_on_all_tables": True,
        "authenticated_read_count_checkpoints": 4,
        "explain_insert_permission_denied": True,
        "explain_update_permission_denied": True,
        "explain_delete_permission_denied": True,
        "negative_dml_test_mutated_records": False,
        "secret_not_logged": True,
        "production_login_provisioned": False,
        "environment_secret_configured": False,
        "backup_with_new_login_executed": False,
    }
    if not isinstance(login, dict) or any(
        login.get(key) != expected for key, expected in login_expect.items()
    ):
        errors.append("isolated backup login evidence missing or overstated")
    storage = doc.get("storage_current_probe")
    storage_expect = {
        "provider": "vercel",
        "project": "mar-p0-recovery-lab",
        "store_id_env_var_present": True,
        "access_scope_account": "404_not_found_or_inaccessible",
        "access_scope_team": "404_not_found_or_inaccessible",
        "store_deletion_confirmed": False,
        "current_blob_read_confirmed": False,
        "provider_worm_90d_confirmed": False,
        "current_backup_and_restore_confirmed": False,
        "reasons_indeterminate": True,
    }
    if not isinstance(storage, dict) or any(
        storage.get(key) != expected for key, expected in storage_expect.items()
    ):
        errors.append("storage 404 cannot establish deletion, retention or backup success")
    if lab.get("authenticated_select_works") is not True:
        errors.append("isolated authenticated read test missing")
    if lab.get("per_table_content_digest_matches_parent") is not True:
        errors.append("clone content equality is not demonstrated")
    source_rows = original.get("rows")
    clone_rows = lab.get("rows")
    for label, inventory in (("source", source_rows), ("clone", clone_rows)):
        if not isinstance(inventory, dict) or set(inventory) != TABLES:
            errors.append(f"{label}: complete three-table row inventory required")
        elif any(
            not isinstance(inventory[key], int)
            or isinstance(inventory[key], bool)
            or inventory[key] != expected
            for key, expected in BASELINE_ROWS.items()
        ):
            errors.append(f"{label}: recorded baseline row counts inconsistent")
    if (isinstance(source_rows, dict) and isinstance(clone_rows, dict)
            and source_rows != clone_rows):
        errors.append("clone and source count mismatch")
    if (probe.get("created") is not False
            or probe.get("production_branch_not_snapshotted") is not True
            or probe.get("error_code") != "not_allowed_to_snapshot_non_root_branch"):
        errors.append("failed isolated snapshot must not be called a restore test")
    if set(required) != REQUIRED or any(value is not False for value in required.values()):
        errors.append("open P0 operational gates must remain explicitly HOLD")
    note = doc.get("notes")
    if not isinstance(note, str) or "Clone/row digests are not a separate backup." not in note:
        errors.append("honest backup limitation missing")
    if not isinstance(doc.get("risks"), list) or len(doc["risks"]) < 5:
        errors.append("baseline risk register incomplete")
    return errors


def main() -> int:
    try:
        record = json.loads(REPORT.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"MAR F02: cannot read baseline: {type(exc).__name__}", file=sys.stderr)
        return 1
    errors = validate_report(record)
    for error in errors:
        print(f"MAR F02: HOLD: {error}", file=sys.stderr)
    if errors:
        return 1
    print("MAR F02: offline audit-record consistency PASS; operational P0 remains HOLD")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
