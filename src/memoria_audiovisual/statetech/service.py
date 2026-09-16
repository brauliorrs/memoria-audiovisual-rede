"""Serviço de aplicação para registrar entidades, evidências e decisões curatoriais."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .contracts import SchemaRegistry
from .entity_decisions import EntityDecision, build_redirect_map
from .evidence import EvidenceRecord
from .ids import stable_id
from .integrity import IntegrityError, IntegrityValidator, LedgerIndex
from .ledger import AtomicLedger
from .models import EntityRecord, ProvenanceRecord, ValidationStatus
from .validation import ContractValidator


class StatetechDataService:
    def __init__(self, ledger: AtomicLedger, schemas: SchemaRegistry) -> None:
        self.ledger = ledger
        self.schemas = schemas
        self.validator = ContractValidator(schemas)
        self.integrity = IntegrityValidator(ledger)

    def register_entity(
        self,
        *,
        entity_type: str,
        natural_key: str,
        payload: dict[str, Any],
        provenance: ProvenanceRecord,
        evidences: tuple[EvidenceRecord, ...] = (),
        previous_version_id: str | None = None,
        referenced_entity_ids: tuple[str, ...] = (),
        validation_status: ValidationStatus = "pending_review",
    ) -> EntityRecord:
        entity_id = stable_id(entity_type, natural_key)
        schema_record = dict(payload)
        schema_record.setdefault(f"{entity_type}_id", entity_id)
        self.validator.validate(entity_type, schema_record)

        entity = EntityRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            payload=schema_record,
            validation_status=validation_status,
            previous_version_id=previous_version_id,
        )
        evidence_payloads = tuple(evidence.to_dict() for evidence in evidences)
        evidence_ids = tuple(str(item["evidence_id"]) for item in evidence_payloads)
        linked_evidence_ids = tuple(dict.fromkeys((*provenance.evidence_ids, *evidence_ids)))

        self.integrity.validate_entity_version(
            entity_id=entity_id,
            version_id=entity.version_id,
            previous_version_id=previous_version_id,
        )
        self.integrity.validate_evidence_ids(evidence_ids)
        self.integrity.validate_entity_references(referenced_entity_ids)
        self.integrity.validate_evidence_references(
            linked_evidence_ids,
            pending_evidence_ids=evidence_ids,
        )

        linked_provenance = replace(
            provenance,
            entity_type=entity_type,
            entity_id=entity_id,
            version_id=entity.version_id,
            validation_status=validation_status,
            evidence_ids=linked_evidence_ids,
            output_record_ids=tuple(
                dict.fromkeys((*provenance.output_record_ids, entity.version_id))
            ),
        )

        records: list[dict[str, Any]] = [
            {"record_type": "entity_version", "payload": entity.to_dict()},
            *({"record_type": "evidence", "payload": item} for item in evidence_payloads),
            {"record_type": "provenance", "payload": linked_provenance.to_dict()},
        ]
        self.ledger.append(records)
        return entity

    def register_entity_decision(self, decision: EntityDecision) -> dict[str, Any]:
        """Valida e persiste uma decisão curatorial como evento append-only."""
        payload = decision.to_dict()
        self.validator.validate("entity_decision", payload)

        index = LedgerIndex.build(self.ledger)
        referenced_entities = tuple(
            dict.fromkeys((*decision.source_entity_ids, *decision.target_entity_ids))
        )
        missing_entities = sorted(set(referenced_entities) - set(index.entities))
        if missing_entities:
            raise IntegrityError(
                f"decisão referencia entidades inexistentes: {', '.join(missing_entities)}"
            )
        self.integrity.validate_evidence_references(decision.evidence_ids)

        existing_decisions = self._entity_decisions()
        decision_id = str(payload["decision_id"])
        if any(item.decision_id == decision_id for item in existing_decisions):
            raise IntegrityError(f"decisão duplicada: {decision_id}")
        if decision.supersedes_decision_id is not None and not any(
            item.decision_id == decision.supersedes_decision_id for item in existing_decisions
        ):
            raise IntegrityError(
                f"decisão substituída inexistente: {decision.supersedes_decision_id}"
            )

        # Verifica conflitos de redirecionamento incluindo a decisão candidata.
        build_redirect_map((*existing_decisions, decision))
        self.ledger.append(({"record_type": "entity_decision", "payload": payload},))
        return payload

    def _entity_decisions(self) -> tuple[EntityDecision, ...]:
        decisions: list[EntityDecision] = []
        for entry in self.ledger.read_all():
            for envelope in entry.records:
                if envelope.get("record_type") != "entity_decision":
                    continue
                payload = dict(envelope.get("payload", {}))
                decisions.append(
                    EntityDecision(
                        decision_type=payload["decision_type"],
                        source_entity_ids=tuple(payload["source_entity_ids"]),
                        target_entity_ids=tuple(payload["target_entity_ids"]),
                        rationale=payload["rationale"],
                        decided_by=payload["decided_by"],
                        evidence_ids=tuple(payload.get("evidence_ids", [])),
                        status=payload["status"],
                        decided_at=payload["decided_at"],
                        supersedes_decision_id=payload.get("supersedes_decision_id"),
                        decision_id=payload["decision_id"],
                    )
                )
        return tuple(decisions)
