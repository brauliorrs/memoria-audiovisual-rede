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
