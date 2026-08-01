"""Índices derivados do ledger para consulta de versões e evidências."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ledger import AtomicLedger


@dataclass(frozen=True, slots=True)
class VersionIndex:
    latest_by_entity: dict[str, dict[str, Any]]
    versions_by_entity: dict[str, tuple[dict[str, Any], ...]]
    evidence_by_id: dict[str, dict[str, Any]]

    @classmethod
    def from_ledger(cls, ledger: AtomicLedger) -> "VersionIndex":
        version_lists: dict[str, list[dict[str, Any]]] = {}
        evidence_by_id: dict[str, dict[str, Any]] = {}
        for transaction in ledger.read_all():
            for record in transaction.records:
                record_type = record.get("record_type")
                payload = dict(record.get("payload", {}))
                if record_type == "entity_version":
                    entity_id = str(payload["entity_id"])
                    version_lists.setdefault(entity_id, []).append(payload)
                elif record_type == "evidence":
                    evidence_by_id[str(payload["evidence_id"])] = payload
        versions = {key: tuple(items) for key, items in version_lists.items()}
        latest = {key: items[-1] for key, items in versions.items() if items}
        return cls(latest_by_entity=latest, versions_by_entity=versions, evidence_by_id=evidence_by_id)

    def latest(self, entity_id: str) -> dict[str, Any] | None:
        return self.latest_by_entity.get(entity_id)
