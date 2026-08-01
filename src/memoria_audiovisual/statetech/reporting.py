"""Exportação validável dos resultados de auditoria de integridade."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .audit import IntegrityIssue, LedgerAuditor
from .contracts import SchemaRegistry
from .ids import stable_id
from .validation import ContractValidator


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _entity_type_for(issue: IntegrityIssue) -> str:
    if issue.rule_code.startswith("EVD-"):
        return "evidence"
    return "institution"


def build_integrity_report(auditor: LedgerAuditor) -> dict[str, Any]:
    issues = auditor.audit()
    errors = sum(issue.severity == "error" for issue in issues)
    warnings = sum(issue.severity == "warning" for issue in issues)
    infos = sum(issue.severity == "info" for issue in issues)
    if errors:
        status = "failed"
    elif warnings:
        status = "passed_with_warnings"
    else:
        status = "passed"

    ledger_entries = auditor.ledger.read_all()
    records_checked = sum(len(entry.records) for entry in ledger_entries)
    issue_rows: list[dict[str, Any]] = []
    for position, issue in enumerate(issues, start=1):
        record_id = issue.record_id or issue.transaction_id or f"unknown-{position}"
        issue_rows.append(
            {
                "issue_id": stable_id(
                    "integrity-issue",
                    f"{issue.rule_code}|{issue.transaction_id}|{record_id}|{position}",
                ),
                "rule_code": issue.rule_code,
                "rule_version": "1.0.0",
                "severity": issue.severity,
                "entity_type": _entity_type_for(issue),
                "record_id": record_id,
                "field_name": None,
                "referenced_entity_type": None,
                "referenced_record_id": None,
                "message": issue.message,
                "resolution_status": "open",
                "resolution_note": None,
            }
        )

    return {
        "schema_version": "1.0.0",
        "generated_at": _now_iso(),
        "status": status,
        "summary": {
            "records_checked": records_checked,
            "errors": errors,
            "warnings": warnings,
            "info": infos,
        },
        "issues": issue_rows,
    }


def export_integrity_report(
    auditor: LedgerAuditor,
    destination: str | Path,
    schemas: SchemaRegistry,
) -> Path:
    report = build_integrity_report(auditor)
    ContractValidator(schemas).validate("integrity_report", report)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path
