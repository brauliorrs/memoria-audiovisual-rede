"""Materialização curatorial de observações confirmadas.

Esta camada não promove sinais automáticos. Somente observações com
``review_status=confirmed`` e ``detection_status=detected`` podem gerar
entidades relacionais. Grupos sem contrato relacional próprio permanecem
registrados como não materializados.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .adapters import AdaptedRecord
from .ids import stable_id
from .models import ProvenanceRecord


TECHNOLOGY_GROUPS = {
    "technology": ("repository_management", "catalogue_software"),
    "api_service": ("api_and_interoperability", "other"),
    "metadata_format": ("metadata_layer", "metadata_management"),
    "interoperability": ("api_and_interoperability", "other"),
    "search": ("search_and_discovery", "search_engine"),
}


@dataclass(frozen=True, slots=True)
class MaterializationDecision:
    observation_id: str
    detector_group: str
    status: str
    reason: str
    record_count: int = 0


@dataclass(frozen=True, slots=True)
class MaterializationResult:
    records: tuple[AdaptedRecord, ...]
    decisions: tuple[MaterializationDecision, ...]

    @property
    def promoted_count(self) -> int:
        return sum(item.status == "promoted" for item in self.decisions)


class CuratorialMaterializer:
    """Converte observações confirmadas em entidades do domínio infraestrutura digital."""

    materializer_name = "curatorial_materializer"
    materializer_version = "1.0.0"

    def materialize(
        self,
        observations: tuple[Mapping[str, Any], ...],
        *,
        institution_ids: Mapping[str, str],
        evidence_ids: Mapping[str, str],
    ) -> MaterializationResult:
        records: list[AdaptedRecord] = []
        decisions: list[MaterializationDecision] = []

        for observation in observations:
            observation_id = str(observation.get("observation_id") or "").strip()
            group = str(observation.get("detector_group") or "").strip()
            corpus_code = str(observation.get("corpus_code") or "").strip()
            value = str(observation.get("detected_value") or "").strip()
            review_status = str(observation.get("review_status") or "").strip()
            detection_status = str(observation.get("detection_status") or "").strip()

            if not observation_id or not group or not corpus_code or not value:
                raise ValueError("observação incompleta para materialização")
            if review_status != "confirmed":
                decisions.append(MaterializationDecision(
                    observation_id, group, "blocked", "review_status_not_confirmed"
                ))
                continue
            if detection_status != "detected":
                decisions.append(MaterializationDecision(
                    observation_id, group, "blocked", "detection_status_not_detected"
                ))
                continue

            institution_id = str(institution_ids.get(corpus_code) or "").strip()
            evidence_id = str(evidence_ids.get(observation_id) or "").strip()
            if not institution_id:
                decisions.append(MaterializationDecision(
                    observation_id, group, "blocked", "institution_id_missing"
                ))
                continue
            if not evidence_id:
                decisions.append(MaterializationDecision(
                    observation_id, group, "blocked", "evidence_id_missing"
                ))
                continue

            if group in TECHNOLOGY_GROUPS:
                generated = self._technology_records(
                    observation, institution_id=institution_id, evidence_id=evidence_id
                )
                records.extend(generated)
                decisions.append(MaterializationDecision(
                    observation_id, group, "promoted", "confirmed_observation", len(generated)
                ))
                continue

            if group == "ai_evidence":
                generated = self._ai_records(
                    observation, institution_id=institution_id, evidence_id=evidence_id
                )
                records.extend(generated)
                decisions.append(MaterializationDecision(
                    observation_id, group, "promoted", "confirmed_ai_observation", len(generated)
                ))
                continue

            decisions.append(MaterializationDecision(
                observation_id, group, "not_materialized", "no_relational_contract_for_group"
            ))

        return MaterializationResult(tuple(records), tuple(decisions))

    def _technology_records(
        self,
        observation: Mapping[str, Any],
        *,
        institution_id: str,
        evidence_id: str,
    ) -> tuple[AdaptedRecord, AdaptedRecord]:
        group = str(observation["detector_group"])
        value = str(observation["detected_value"])
        stack_layer, provider_role = TECHNOLOGY_GROUPS[group]
        technology_key = f"{group}|{value.casefold()}"
        technology_id = stable_id("technology", technology_key)
        relation_key = f"{institution_id}|{technology_id}|{group}"
        relation_id = stable_id("institution_technology_relation", relation_key)
        observed_at = str(observation.get("observed_at") or "") or None

        technology_payload = {
            "technology_id": technology_id,
            "name": value,
            "version": None,
            "stack_layer": stack_layer,
            "technology_function": group,
            "deployment_model": "unknown",
            "ownership_model": "unknown",
            "hosting_location": None,
            "data_residency_country": None,
            "critical_dependency": None,
            "evidence_ids": [evidence_id],
            "validation_status": "confirmed",
        }
        relation_payload = {
            "relation_id": relation_id,
            "institution_id": institution_id,
            "technology_id": technology_id,
            "provider_id": None,
            "provider_role": provider_role,
            "provider_relationship": "unknown",
            "relationship_start_date": None,
            "relationship_end_date": None,
            "evidence_id": evidence_id,
            "confidence": str(observation.get("automatic_confidence") or "unknown"),
            "validation_status": "confirmed",
            "reviewer_note": str(observation.get("review_note") or "") or None,
        }
        source_observation_id = str(observation["observation_id"])
        return (
            AdaptedRecord(
                entity_type="technology",
                natural_key=technology_key,
                payload=technology_payload,
                provenance=self._provenance(
                    entity_type="technology",
                    natural_key=technology_key,
                    observation_id=source_observation_id,
                    evidence_id=evidence_id,
                    observed_at=observed_at,
                ),
            ),
            AdaptedRecord(
                entity_type="institution_technology_relation",
                natural_key=relation_key,
                payload=relation_payload,
                provenance=self._provenance(
                    entity_type="institution_technology_relation",
                    natural_key=relation_key,
                    observation_id=source_observation_id,
                    evidence_id=evidence_id,
                    observed_at=observed_at,
                ),
                referenced_entity_ids=(institution_id, technology_id),
            ),
        )

    def _ai_records(
        self,
        observation: Mapping[str, Any],
        *,
        institution_id: str,
        evidence_id: str,
    ) -> tuple[AdaptedRecord, ...]:
        value = str(observation["detected_value"])
        natural_key = f"{institution_id}|{value.casefold()}"
        ai_system_id = stable_id("ai_system", natural_key)
        payload = {
            "ai_system_id": ai_system_id,
            "name": value,
            "provider_id": None,
            "institution_id": institution_id,
            "function": "unknown",
            "model_type": None,
            "deployment_stage": "unknown",
            "human_oversight": "unknown",
            "training_data_disclosure": "unknown",
            "automated_output_public": None,
            "algorithmic_transparency": "unknown",
            "impact_area": "cataloguing_or_metadata",
            "evidence_ids": [evidence_id],
            "validation_status": "confirmed",
        }
        return (AdaptedRecord(
            entity_type="ai_system",
            natural_key=natural_key,
            payload=payload,
            provenance=self._provenance(
                entity_type="ai_system",
                natural_key=natural_key,
                observation_id=str(observation["observation_id"]),
                evidence_id=evidence_id,
                observed_at=str(observation.get("observed_at") or "") or None,
            ),
            referenced_entity_ids=(institution_id,),
        ),)

    def _provenance(
        self,
        *,
        entity_type: str,
        natural_key: str,
        observation_id: str,
        evidence_id: str,
        observed_at: str | None,
    ) -> ProvenanceRecord:
        return ProvenanceRecord(
            provenance_id=stable_id("provenance", f"materialize|{entity_type}|{natural_key}"),
            entity_type=entity_type,
            entity_id=stable_id(entity_type, natural_key),
            activity_type="curatorial_materialization",
            agent_type="script",
            source_ids=(observation_id,),
            evidence_ids=(evidence_id,),
            method="confirmed_observation_to_relational_entity",
            tool_or_script=self.materializer_name,
            tool_version=self.materializer_version,
            observed_at=observed_at,
            change_origin="empirical_change",
            validation_status="confirmed",
            notes="Materialização permitida somente após confirmação curatorial explícita.",
        )
