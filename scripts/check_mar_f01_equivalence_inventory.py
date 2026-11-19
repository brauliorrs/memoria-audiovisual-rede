#!/usr/bin/env python3
"""Check that F01 migration audit is traceable without inventing equivalence."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/engineering/mar-f01-functional-equivalence-inventory.json"
STATUS = {"snapshot_supported", "partial", "operational_missing", "blocked_by_rights"}
SOURCE = {"app/streamlit_app.py", "src/memoria_audiovisual/inclusion_queue.py",
          "src/memoria_audiovisual/corpus_admission_engine.py",
          "scripts/run_observatory_cycle.py", "scripts/build_mar_site_projections_b2.py"}
ID_RE = re.compile(r"^[MB][0-9]{2}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def check_inventory(document: object, root: Path = ROOT) -> list[str]:
    """Validate inventory shape and checked claims; never decide scientific merit."""
    issues: list[str] = []
    if not isinstance(document, dict):
        return ["inventory must be an object"]
    if document.get("schema") != "mar.f01.functional-equivalence-inventory.v1":
        issues.append("unknown inventory schema")
    sha = document.get("based_on_commit")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        issues.append("invalid source baseline SHA")
    if document.get("scope") != "audit_only_no_functional_acceptance":
        issues.append("F01 inventory cannot declare a functional acceptance without gate evidence")
    if document.get("release_authorized") is not False:
        issues.append("migration audit cannot authorize release")
    rows = document.get("flows")
    if not isinstance(rows, list) or not rows:
        return issues + ["flows must be a non-empty list"]
    seen: set[str] = set()
    for index, row in enumerate(rows):
        tag = f"row {index}"
        if not isinstance(row, dict):
            issues.append(f"{tag}: must be object")
            continue
        identifier = row.get("id")
        tag = str(identifier)
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            issues.append(f"{tag}: invalid ID")
        elif identifier in seen:
            issues.append(f"{tag}: repeated ID")
        else:
            seen.add(identifier)
        if not isinstance(row.get("name"), str) or not row["name"].strip():
            issues.append(f"{tag}: missing name")
        if row.get("status") not in STATUS:
            issues.append(f"{tag}: invalid status")
        if row.get("source") not in SOURCE:
            issues.append(f"{tag}: unrecognized source")
        marker = row.get("anchor")
        if not isinstance(marker, str):
            issues.append(f"{tag}: anchor must be string")
        if row.get("source") == "app/streamlit_app.py" and not marker:
            issues.append(f"{tag}: Streamlit flow requires a source marker")
        if not isinstance(row.get("gap"), str) or len(row["gap"].strip()) < 15:
            issues.append(f"{tag}: unresolved acceptance/risk detail")
        paths = [row.get("source")]
        for key in ("target", "data", "existing_tests"):
            value = row.get(key)
            if not isinstance(value, list) or any(
                not isinstance(p, str) for p in value
            ):
                issues.append(f"{tag}: {key} must be list of paths")
            else:
                paths.extend(value)
        for path in paths:
            if not isinstance(path, str):
                continue
            full = (root / path).resolve()
            if not full.is_relative_to(root.resolve()):
                issues.append(f"{tag}: invalid path outside repository")
            elif not full.is_file():
                issues.append(f"{tag}: nonexistent file: {path}")
        source = row.get("source")
        if source in SOURCE and isinstance(marker, str) and marker:
            full = root / source
            if full.is_file() and marker not in full.read_text(encoding="utf-8"):
                issues.append(f"{tag}: missing exact marker in source")
        if row.get("status") == "operational_missing" and row.get("target"):
            issues.append(f"{tag}: operational_missing cannot declare destination")
        if row.get("status") == "snapshot_supported" and not row.get("target"):
            issues.append(f"{tag}: snapshot_supported needs destination")
        if row.get("evidence_level") != "source_and_destination_inspected_not_equivalence_proven":
            issues.append(f"{tag}: unsupported evidence level")
        if row.get("scientific_release_authorized") is not False:
            issues.append(f"{tag}: inventory cannot grant scientific release")
        if row.get("equivalence_accepted") is not False or row.get("acceptance_evidence") is not None:
            issues.append(f"{tag}: functional sign-off belongs in human stage gate, not inventory")
    if len(seen) < 20:
        issues.append("F01 inventory unexpectedly covers too few distinct flows")
    if not any(row.get("source") == "app/streamlit_app.py" for row in rows if isinstance(row, dict)):
        issues.append("Streamlit migration source missing")
    if not any(row.get("source") != "app/streamlit_app.py" for row in rows if isinstance(row, dict)):
        issues.append("Python operational source missing")
    legacy = root / "app/streamlit_app.py"
    if legacy.is_file():
        code = legacy.read_text(encoding="utf-8")
        definitions = set(re.findall(r"^def ([A-Za-z_][A-Za-z0-9_]*)\\(", code, flags=re.MULTILINE))
        expected = {
            "render_function_coverage": {
                fn for fn in definitions if fn.startswith("render_")
            },
            "data_helper_coverage": {
                fn for fn in definitions
                if fn.startswith(("build_", "load_"))
            },
        }
        expected["support_function_coverage"] = (
            definitions - expected["render_function_coverage"]
            - expected["data_helper_coverage"]
        )
        for key, symbols in expected.items():
            actual = document.get(key)
            if not isinstance(actual, dict):
                issues.append(f"{key}: missing coverage mapping")
                continue
            if set(actual) != symbols:
                issues.append(f"{key}: missing or extra symbols: "
                              f"{sorted(symbols ^ set(actual))}")
            if any(value not in seen for value in actual.values()):
                issues.append(f"{key}: coverage references unknown flow ID")
        expected_tabs = {line.strip() for line in code.splitlines() if "st.tabs(" in line}
        actual_tabs = document.get("ui_tab_coverage")
        if not isinstance(actual_tabs, dict):
            issues.append("ui_tab_coverage: missing tab mapping")
        else:
            if set(actual_tabs) != expected_tabs:
                issues.append("ui_tab_coverage: missing or extra tabs: "
                              f"{sorted(expected_tabs ^ set(actual_tabs))}")
            if any(value not in seen for value in actual_tabs.values()):
                issues.append("ui_tab_coverage: unknown flow ID")
    return issues


def main() -> int:
    try:
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"F01 HOLD: cannot read inventory: {exc}", file=sys.stderr)
        return 1
    problems = check_inventory(inventory)
    for error in problems:
        print("F01 HOLD: " + error, file=sys.stderr)
    if problems:
        return 1
    print(f"F01 structural inventory PASS ({len(inventory['flows'])} mapped); "
          "not a functional, scientific or publication acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
