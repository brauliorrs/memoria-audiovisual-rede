"""Auditoria reconstruível da integridade histórica do ledger."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .ledger import AtomicLedger

Severity = Literal["error", "warning", "info"]


@dataclass(frozen=True, slots=True)
class IntegrityIssue:
    rule_code: str
    severity: Severity
    transaction_id: str | None
    record_id: str | None
    message: str

    def to_dict(self) -> dict[str, str | None]:
        return asdict(self)


class LedgerAuditor:
    def __init__(self, ledger: AtomicLedger) -> None:
        self.ledger = ledger

    def audit(self) -> tuple[IntegrityIssue, ...]:
        issues: list[IntegrityIssue] = []
        versions: set[str] = set()
        evidences: set[str] = set()
        latest: dict[str, str] = {}

        for entry in self.ledger.read_all():
            transaction_evidences: set[str] = set()
            for envelope in entry.records:
                record_type = envelope.get("record_type")
                payload = envelope.get("payload", {})
                if record_type == "evidence":
                    evidence_id = str(payload.get("evidence_id", ""))
                    if not evidence_id:
                        issues.append(IntegrityIssue("EVD-001", "error", entry.transaction_id, None, "evidência sem identificador"))
                    elif evidence_id in evidences or evidence_id in transaction_evidences:
                        issues.append(IntegrityIssue("EVD-002", "warning", entry.transaction_id, evidence_id, "evidência duplicada"))
                    transaction_evidences.add(evidence_id)

            available_evidences = evidences | transaction_evidences
            for envelope in entry.records:
                record_type = envelope.get("record_type")
                payload = envelope.get("payload", {})
                if record_type == "entity_version":
                    entity_id = str(payload.get("entity_id", ""))
                    version_id = str(payload.get("version_id", ""))
                    previous = payload.get("previous_version_id")
                    if not entity_id or not version_id:
                        issues.append(IntegrityIssue("REF-001", "error", entry.transaction_id, version_id or None, "versão sem entity_id ou version_id"))
                        continue
                    if version_id in versions:
                        issues.append(IntegrityIssue("VER-001", "error", entry.transaction_id, version_id, "version_id duplicado"))
                    expected = latest.get(entity_id)
                    if expected is None and previous is not None:
                        issues.append(IntegrityIssue("VER-002", "error", entry.transaction_id, version_id, "primeira versão aponta para predecessor"))
                    elif expected is not None and previous != expected:
                        issues.append(IntegrityIssue("VER-003", "error", entry.transaction_id, version_id, f"predecessor esperado: {expected}"))
                    versions.add(version_id)
                    latest[entity_id] = version_id
                elif record_type == "provenance":
                    for evidence_id in payload.get("evidence_ids", []):
                        if str(evidence_id) not in available_evidences:
                            issues.append(IntegrityIssue("EVD-003", "error", entry.transaction_id, str(payload.get("provenance_id") or ""), f"referência de evidência órfã: {evidence_id}"))

            evidences.update(transaction_evidences)

        return tuple(issues)
