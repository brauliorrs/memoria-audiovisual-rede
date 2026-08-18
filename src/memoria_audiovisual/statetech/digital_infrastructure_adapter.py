"""Adaptador da auditoria heurística de infraestrutura para o contrato Estado–tecnologia.

A coleta legada permanece responsável por observar a superfície pública. Este módulo
normaliza cada resultado em registros longos compatíveis com
``schemas/digital_infrastructure_audit.schema.json`` e com o ledger append-only.
Nenhuma detecção automatizada é promovida a resultado científico: todo registro
entra como ``pending_review``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from .adapters import AdaptedRecord
from .evidence import EvidenceRecord
from .ids import stable_id
from .models import ProvenanceRecord

ADAPTER_NAME = "digital_infrastructure_audit"
ADAPTER_VERSION = "2.0.0"
DETECTOR_VERSION = "1.0.0"
ENTITY_TYPE = "digital_infrastructure_audit"

PUBLISHABLE_REVIEW_STATUSES = frozenset({"confirmed", "probable"})
REVIEWED_STATUSES = frozenset(
    {"confirmed", "probable", "inconclusive", "false_positive", "not_assessable"}
)


@dataclass(frozen=True, slots=True)
class DetectorSpec:
    detector_group: str
    detector_id: str
    source_field: str
    empty_value: str
    evidence_source: str
    evidence_field: str | None = None


DETECTOR_SPECS = (
    DetectorSpec("technology", "cms_signature", "cms", "cms_signal", "html"),
    DetectorSpec("api_service", "api_surface", "api_types", "public_api_signal", "link", "api_evidence"),
    DetectorSpec("metadata_format", "metadata_surface", "metadata_formats", "metadata_format_signal", "metadata"),
    DetectorSpec(
        "interoperability",
        "interoperability_surface",
        "interoperability_protocols",
        "interoperability_signal",
        "metadata",
    ),
    DetectorSpec("search", "search_surface", "search_mechanisms", "search_signal", "form"),
    DetectorSpec("restriction", "restriction_surface", "access_restrictions", "access_restriction_signal", "text"),
)


def _split_values(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(part.strip() for part in str(value).split("|") if part.strip())


def _collection_status(source: Mapping[str, Any]) -> str:
    if bool(source.get("reachable")):
        return "success"
    status = source.get("http_status")
    if status in {401, 403, 429}:
        return "blocked"
    error = str(source.get("error") or "").lower()
    if "timeout" in error or "timed out" in error:
        return "timeout"
    return "error"


def _safe_url(value: Any, fallback: str) -> str:
    text = str(value or "").strip()
    return text or fallback


def _observation_id(source: Mapping[str, Any]) -> str:
    natural_key = "|".join(
        (
            str(source["snapshot_id"]),
            str(source["corpus_code"]),
            str(source["source_url"]),
        )
    )
    return stable_id("digital_infrastructure_observation", natural_key)


def _make_detection(
    *,
    source: Mapping[str, Any],
    observation_id: str,
    detector_group: str,
    detector_id: str,
    detected_value: str,
    detection_status: str,
    evidence_source: str,
    evidence_value: str | None,
    automatic_confidence: str,
) -> AdaptedRecord:
    evidence_url = _safe_url(source.get("final_url"), str(source["source_url"]))
    payload: dict[str, Any] = {
        "observation_id": observation_id,
        "snapshot_id": str(source["snapshot_id"]),
        "observed_at": str(source["checked_at_utc"]),
        "corpus_code": str(source["corpus_code"]),
        "institution_name": str(source["institution"]),
        "entity_level": str(source.get("entity_level") or "institution"),
        "country": source.get("country") or None,
        "source_url": str(source["source_url"]),
        "final_url": str(source.get("final_url") or "") or None,
        "http_status": source.get("http_status"),
        "collection_status": _collection_status(source),
        "detector_group": detector_group,
        "detected_value": detected_value,
        "detection_status": detection_status,
        "automatic_confidence": automatic_confidence,
        "detector_id": detector_id,
        "detector_version": DETECTOR_VERSION,
        "evidence_source": evidence_source,
        "evidence_value": evidence_value or None,
        "evidence_url": evidence_url,
        "review_status": "pending_review",
        "reviewed_at": None,
        "reviewer": None,
        "review_note": None,
        "supporting_source": None,
    }

    natural_key = "|".join(
        (
            observation_id,
            detector_id,
            detected_value,
        )
    )
    entity_id = stable_id(ENTITY_TYPE, natural_key)
    evidence = EvidenceRecord(
        evidence_url=evidence_url,
        evidence_type=detector_group,
        collection_method="public_surface_heuristic",
        source_title=str(source.get("institution") or "") or None,
        source_organization=str(source.get("institution") or "") or None,
        observation_date=str(source["checked_at_utc"]),
        evidence_excerpt=evidence_value or None,
        confidence=automatic_confidence,
        validation_status="pending_review",
        metadata={
            "snapshot_id": str(source["snapshot_id"]),
            "corpus_code": str(source["corpus_code"]),
            "detector_id": detector_id,
            "detector_version": DETECTOR_VERSION,
            "detection_status": detection_status,
        },
    )
    evidence_id = str(evidence.to_dict()["evidence_id"])
    provenance = ProvenanceRecord(
        provenance_id=stable_id("provenance", natural_key),
        entity_type=ENTITY_TYPE,
        entity_id=entity_id,
        activity_type="automated_observation",
        agent_type="software",
        validation_status="pending_review",
        source_ids=(str(source["source_url"]),),
        evidence_ids=(evidence_id,),
        method="heuristic_public_surface_audit",
        tool_or_script="scripts/audit_digital_infrastructure.py",
        tool_version=ADAPTER_VERSION,
        code_commit_sha=str(source.get("code_commit_sha") or "") or None,
        parameters={
            "snapshot_id": str(source["snapshot_id"]),
            "corpus_code": str(source["corpus_code"]),
            "detector_id": detector_id,
            "detector_version": DETECTOR_VERSION,
        },
        observed_at=str(source["checked_at_utc"]),
        change_origin="automated_collection",
        notes="Detecção heurística; requer validação curatorial antes de publicação científica.",
    )
    return AdaptedRecord(
        entity_type=ENTITY_TYPE,
        natural_key=natural_key,
        payload=payload,
        provenance=provenance,
        evidences=(evidence,),
    )


class DigitalInfrastructureAuditAdapter:
    """Converte uma observação legada em uma linha por detector/evidência."""

    adapter_name = ADAPTER_NAME
    adapter_version = ADAPTER_VERSION

    def adapt(self, source: Mapping[str, Any]) -> tuple[AdaptedRecord, ...]:
        required = ("snapshot_id", "corpus_code", "institution", "source_url", "checked_at_utc")
        missing = [field for field in required if not str(source.get(field) or "").strip()]
        if missing:
            raise ValueError(f"campos obrigatórios ausentes no adaptador: {', '.join(missing)}")

        observation_id = _observation_id(source)
        reachable = bool(source.get("reachable"))
        records: list[AdaptedRecord] = []

        for spec in DETECTOR_SPECS:
            values = _split_values(source.get(spec.source_field))
            if spec.detector_id == "cms_signature" and values and values[0].lower().startswith("não identificado"):
                values = ()
            evidence_value = str(source.get(spec.evidence_field) or "").strip() if spec.evidence_field else ""
            if values:
                for value in values:
                    records.append(
                        _make_detection(
                            source=source,
                            observation_id=observation_id,
                            detector_group=spec.detector_group,
                            detector_id=spec.detector_id,
                            detected_value=value,
                            detection_status="detected",
                            evidence_source=spec.evidence_source,
                            evidence_value=evidence_value or value,
                            automatic_confidence="medium",
                        )
                    )
            else:
                records.append(
                    _make_detection(
                        source=source,
                        observation_id=observation_id,
                        detector_group=spec.detector_group,
                        detector_id=spec.detector_id,
                        detected_value=spec.empty_value,
                        detection_status="not_detected" if reachable else "unknown",
                        evidence_source=spec.evidence_source,
                        evidence_value=evidence_value or None,
                        automatic_confidence="low",
                    )
                )

        ai_evidence = str(source.get("ai_cataloguing_evidence") or "").strip()
        ai_detected = bool(ai_evidence) or str(source.get("ai_cataloguing_status") or "").lower().startswith(
            "evidência pública"
        )
        records.append(
            _make_detection(
                source=source,
                observation_id=observation_id,
                detector_group="ai_evidence",
                detector_id="declared_ai_surface",
                detected_value="declared_ai_cataloguing" if ai_detected else "declared_ai_signal",
                detection_status="detected" if ai_detected else ("not_detected" if reachable else "unknown"),
                evidence_source="text",
                evidence_value=ai_evidence or None,
                automatic_confidence="medium" if ai_detected else "low",
            )
        )
        return tuple(records)


def adapted_payload_rows(records: tuple[AdaptedRecord, ...]) -> list[dict[str, Any]]:
    return [dict(record.payload) for record in records]


def curated_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retém decisões humanas registradas; exclui pendências e falsos positivos."""
    return [
        dict(row)
        for row in rows
        if row.get("review_status") in REVIEWED_STATUSES and row.get("review_status") != "false_positive"
    ]


def publishable_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Retém apenas evidências aptas a alimentar indicadores públicos."""
    return [dict(row) for row in rows if row.get("review_status") in PUBLISHABLE_REVIEW_STATUSES]
