"""Modelos mínimos da Fase 1, sem dependências externas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

from .ids import version_id

ValidationStatus = Literal[
    "pending_review",
    "confirmed",
    "probable",
    "inconclusive",
    "false_positive",
    "not_assessable",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class EntityRecord:
    entity_type: str
    entity_id: str
    payload: dict[str, Any]
    validation_status: ValidationStatus = "pending_review"
    recorded_at: str = field(default_factory=utc_now_iso)
    schema_version: str = "1.0.0"
    previous_version_id: str | None = None

    @property
    def version_id(self) -> str:
        version_payload = {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "validation_status": self.validation_status,
            "schema_version": self.schema_version,
        }
        return version_id(self.entity_id, version_payload)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["version_id"] = self.version_id
        return data


@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    provenance_id: str
    entity_type: str
    entity_id: str
    activity_type: str
    agent_type: str
    validation_status: ValidationStatus = "pending_review"
    version_id: str | None = None
    source_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    input_artifact_ids: tuple[str, ...] = ()
    output_record_ids: tuple[str, ...] = ()
    method: str | None = None
    tool_or_script: str | None = None
    tool_version: str | None = None
    code_commit_sha: str | None = None
    parameters: dict[str, Any] | None = None
    agent_id: str | None = None
    recorded_at: str = field(default_factory=utc_now_iso)
    observed_at: str | None = None
    reviewed_at: str | None = None
    previous_provenance_id: str | None = None
    change_origin: str | None = None
    schema_version: str = "1.0.0"
    data_contract_version: str = "1.0.0"
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for field_name in ("source_ids", "evidence_ids", "input_artifact_ids", "output_record_ids"):
            data[field_name] = list(data[field_name])
        return data
