"""Revisão curatorial versionada para a auditoria de infraestrutura digital."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from .adapters import AdaptedRecord
from .ids import stable_id
from .models import ProvenanceRecord, ValidationStatus
from .service import StatetechDataService

REVIEWABLE_STATUSES: frozenset[ValidationStatus] = frozenset(
    {"confirmed", "probable", "inconclusive", "false_positive", "not_assessable"}
)
NOTE_REQUIRED = frozenset({"probable", "inconclusive", "false_positive", "not_assessable"})


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def register_infrastructure_review(
    service: StatetechDataService,
    *,
    source_record: AdaptedRecord,
    previous_version_id: str,
    review_status: ValidationStatus,
    reviewer: str,
    review_note: str | None = None,
    supporting_source: str | None = None,
    reviewed_at: str | None = None,
):
    """Acrescenta uma decisão humana sem sobrescrever a observação automatizada.

    A evidência original permanece no ledger. A revisão cria uma nova versão da
    mesma entidade e uma nova proveniência que referencia a evidência já registrada.
    """
    if review_status not in REVIEWABLE_STATUSES:
        raise ValueError("review_status deve representar uma decisão curatorial final")
    reviewer = reviewer.strip()
    if not reviewer:
        raise ValueError("reviewer é obrigatório")
    note = (review_note or "").strip() or None
    if review_status in NOTE_REQUIRED and note is None:
        raise ValueError(f"review_note é obrigatório para {review_status}")

    timestamp = reviewed_at or utc_now_iso()
    payload = dict(source_record.payload)
    payload.update(
        {
            "review_status": review_status,
            "reviewed_at": timestamp,
            "reviewer": reviewer,
            "review_note": note,
            "supporting_source": supporting_source,
        }
    )

    provenance_key = f"{source_record.natural_key}|review|{timestamp}|{reviewer}|{review_status}"
    provenance = ProvenanceRecord(
        provenance_id=stable_id("provenance", provenance_key),
        entity_type=source_record.entity_type,
        entity_id=stable_id(source_record.entity_type, source_record.natural_key),
        activity_type="human_review",
        agent_type="human",
        validation_status=review_status,
        source_ids=source_record.provenance.source_ids,
        evidence_ids=source_record.provenance.evidence_ids,
        method="curatorial_validation_protocol",
        tool_or_script="src/memoria_audiovisual/statetech/digital_infrastructure_review.py",
        tool_version="1.0.0",
        parameters={"review_status": review_status},
        agent_id=reviewer,
        observed_at=source_record.provenance.observed_at,
        reviewed_at=timestamp,
        previous_provenance_id=source_record.provenance.provenance_id,
        change_origin="human_review",
        notes=note,
    )

    return service.register_entity(
        entity_type=source_record.entity_type,
        natural_key=source_record.natural_key,
        payload=payload,
        provenance=provenance,
        evidences=(),
        previous_version_id=previous_version_id,
        referenced_entity_ids=source_record.referenced_entity_ids,
        validation_status=review_status,
    )
