"""Entidades executáveis de evidência e artefatos observados."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .ids import stable_id
from .models import ValidationStatus, utc_now_iso


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    evidence_url: str
    evidence_type: str
    collection_method: str
    source_title: str | None = None
    source_organization: str | None = None
    evidence_date: str | None = None
    observation_date: str = field(default_factory=utc_now_iso)
    evidence_excerpt: str | None = None
    confidence: str = "unknown"
    validation_status: ValidationStatus = "pending_review"
    reviewer_note: str | None = None
    metadata: dict[str, Any] | None = None
    evidence_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_id"] = self.evidence_id or stable_id(
            "evidence", f"{self.evidence_url}|{self.observation_date}|{self.evidence_type}"
        )
        return data
