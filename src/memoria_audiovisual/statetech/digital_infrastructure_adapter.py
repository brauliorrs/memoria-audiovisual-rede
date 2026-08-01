"""Adapta a auditoria heurística existente ao núcleo Estado–tecnologia.

O adaptador não coleta, não persiste e não publica. Ele transforma uma
``InfrastructureAudit`` já produzida em observações normalizadas, incluindo um
estado explícito para cada grupo de parâmetro esperado.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict
from typing import Any

from memoria_audiovisual.digital_infrastructure_audit import InfrastructureAudit

from .adapters import AdaptedRecord
from .evidence import EvidenceRecord
from .ids import stable_id
from .models import ProvenanceRecord
from .parameter_coverage import EXPECTED_DETECTOR_GROUPS


def _split_pipe(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    return tuple(item.strip() for item in str(value).split("|") if item and item.strip())


def _as_mapping(source: InfrastructureAudit | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(source, InfrastructureAudit):
        return asdict(source)
    return dict(source)


class DigitalInfrastructureAuditAdapter:
    """Converte uma auditoria agregada em observações por sinal e por ausência."""

    adapter_name = "digital_infrastructure_audit"
    adapter_version = "1.1.0"
    detector_version = "1.1.0"

    def __init__(self, *, snapshot_id: str, entity_level: str = "corpus") -> None:
        if not snapshot_id.strip():
            raise ValueError("snapshot_id não pode ser vazio")
        if not entity_level.strip():
            raise ValueError("entity_level não pode ser vazio")
        self.snapshot_id = snapshot_id
        self.entity_level = entity_level

    def adapt(
        self, source: InfrastructureAudit | Mapping[str, Any]
    ) -> tuple[AdaptedRecord, ...]:
        raw = _as_mapping(source)
        corpus_code = str(raw.get("corpus_code") or "").strip()
        institution = str(raw.get("institution") or "").strip()
        source_url = str(raw.get("source_url") or "").strip()
        observed_at = str(raw.get("checked_at_utc") or "").strip()
        if not corpus_code or not institution or not source_url or not observed_at:
            raise ValueError(
                "a auditoria exige corpus_code, institution, source_url e checked_at_utc"
            )

        final_url = str(raw.get("final_url") or "").strip() or None
        reachable = bool(raw.get("reachable"))
        collection_status = "success" if reachable else "error"
        evidence_url = final_url or source_url

        detections = list(self._detections(raw))
        detected_groups = {item[0] for item in detections}
        for group in EXPECTED_DETECTOR_GROUPS:
            if group in detected_groups:
                continue
            detections.append((
                group,
                "not_detected" if reachable else "not_assessable",
                "not_detected" if reachable else "unknown",
                "low",
                "html",
                None,
            ))

        records: list[AdaptedRecord] = []
        for detector_group, value, status, confidence, evidence_source, evidence_value in detections:
            natural_key = "|".join(
                [self.snapshot_id, corpus_code, source_url, detector_group, value]
            )
            observation_id = stable_id("infrastructure-observation", natural_key)
            review_status = "pending_review" if reachable else "not_assessable"
            payload: dict[str, Any] = {
                "observation_id": observation_id,
                "snapshot_id": self.snapshot_id,
                "observed_at": observed_at,
                "corpus_code": corpus_code,
                "institution_name": institution,
                "entity_level": self.entity_level,
                "country": raw.get("country"),
                "source_url": source_url,
                "final_url": final_url,
                "http_status": raw.get("http_status"),
                "collection_status": collection_status,
                "detector_group": detector_group,
                "detected_value": value,
                "detection_status": status,
                "automatic_confidence": confidence,
                "detector_id": f"digital_infrastructure.{detector_group}",
                "detector_version": self.detector_version,
                "evidence_source": evidence_source,
                "evidence_value": evidence_value,
                "evidence_url": evidence_url,
                "review_status": review_status,
                "reviewed_at": None,
                "reviewer": None,
                "review_note": str(raw.get("error") or "").strip() or None,
                "supporting_source": None,
            }
            evidence = EvidenceRecord(
                evidence_url=evidence_url,
                evidence_type=self._evidence_type(evidence_source),
                collection_method="public_web_audit",
                source_title=f"Auditoria técnica: {institution}",
                source_organization=institution,
                observation_date=observed_at,
                evidence_excerpt=evidence_value,
                confidence=confidence if confidence in {"high", "low"} else "moderate",
                validation_status=review_status,
                metadata={
                    "observation_id": observation_id,
                    "detector_group": detector_group,
                    "corpus_code": corpus_code,
                    "detection_status": status,
                },
            )
            evidence_payload = evidence.to_dict()
            provenance = ProvenanceRecord(
                provenance_id=stable_id("provenance", observation_id),
                entity_type="digital_infrastructure_audit",
                entity_id=observation_id,
                activity_type="adaptation",
                agent_type="script",
                source_ids=(stable_id("source", source_url),),
                evidence_ids=(str(evidence_payload["evidence_id"]),),
                method="heuristic_public_surface_audit",
                tool_or_script=self.adapter_name,
                tool_version=self.adapter_version,
                parameters={
                    "snapshot_id": self.snapshot_id,
                    "entity_level": self.entity_level,
                    "expected_detector_groups": list(EXPECTED_DETECTOR_GROUPS),
                },
                observed_at=observed_at,
                change_origin="empirical_change",
                notes=(
                    "Observação explícita de detecção, não detecção ou impossibilidade de avaliação; "
                    "pendente de revisão quando a superfície foi alcançada."
                ),
            )
            records.append(AdaptedRecord(
                entity_type="digital_infrastructure_audit",
                natural_key=natural_key,
                payload=payload,
                provenance=provenance,
                evidences=(evidence,),
            ))
        return tuple(records)

    def _detections(
        self, raw: Mapping[str, Any]
    ) -> Iterable[tuple[str, str, str, str, str, str | None]]:
        cms = str(raw.get("cms") or "").strip()
        if cms and cms != "Não identificado":
            yield ("technology", cms, "detected", "medium", "html", cms)
        for value in _split_pipe(raw.get("api_types")):
            yield (
                "api_service", value, "detected", "medium", "url_pattern",
                str(raw.get("api_evidence") or "").strip() or value,
            )
        for value in _split_pipe(raw.get("metadata_formats")):
            yield ("metadata_format", value, "detected", "medium", "metadata", value)
        for value in _split_pipe(raw.get("interoperability_protocols")):
            yield ("interoperability", value, "detected", "medium", "metadata", value)
        for value in _split_pipe(raw.get("search_mechanisms")):
            yield ("search", value, "detected", "medium", "form", value)
        for value in _split_pipe(raw.get("access_restrictions")):
            yield ("restriction", value, "detected", "low", "text", value)
        ai_evidence = str(raw.get("ai_cataloguing_evidence") or "").strip()
        if ai_evidence:
            yield (
                "ai_evidence",
                str(raw.get("ai_cataloguing_status") or "public_text_signal"),
                "detected", "low", "text", ai_evidence,
            )

    @staticmethod
    def _evidence_type(evidence_source: str) -> str:
        return {
            "header": "http_header",
            "metadata": "technical_metadata",
            "script": "source_code",
            "url_pattern": "api_documentation",
        }.get(evidence_source, "official_webpage")
