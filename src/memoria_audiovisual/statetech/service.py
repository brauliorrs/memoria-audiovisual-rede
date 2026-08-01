"""Serviço de aplicação para registrar entidades, evidências e proveniência."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .contracts import SchemaRegistry
from .evidence import EvidenceRecord
from .ids import stable_id
from .ledger import AtomicLedger
from .models import EntityRecord, ProvenanceRecord
from .validation import ContractValidator


class StatetechDataService:
    def __init__(self, ledger: AtomicLedger, schemas: SchemaRegistry) -> None:
        self.ledger = ledger
        self.schemas = schemas
        self.validator = ContractValidator(schemas)

    def register_entity(
        self,
        *,
        entity_type: str,
        natural_key: str,
        payload: dict[str, Any],
        provenance: ProvenanceRecord,
        evidences: tuple[EvidenceRecord, ...] = (),
        previous_version_id: str | None = None,
    ) -> EntityRecord:
        entity_id = stable_id(entity_type, natural_key)
        schema_record = dict(payload)
        schema_record.setdefault(f"{entity_type}_id", entity_id)
        self.validator.validate(entity_type, schema_record)

        entity = EntityRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            payload=schema_record,
            previous_version_id=previous_version_id,
        )
        evidence_payloads = tuple(evidence.to_dict() for evidence in evidences)
        evidence_ids = tuple(str(item["evidence_id"]) for item in evidence_payloads)
        linked_provenance = replace(
            provenance,
            entity_type=entity_type,
            entity_id=entity_id,
            version_id=entity.version_id,
            evidence_ids=tuple(dict.fromkeys((*provenance.evidence_ids, *evidence_ids))),
            output_record_ids=tuple(dict.fromkeys((*provenance.output_record_ids, entity.version_id))),
        )

        records: list[dict[str, Any]] = [
            {"record_type": "entity_version", "payload": entity.to_dict()},
            *({"record_type": "evidence", "payload": item} for item in evidence_payloads),
            {"record_type": "provenance", "payload": linked_provenance.to_dict()},
        ]
        self.ledger.append(records)
        return entity
