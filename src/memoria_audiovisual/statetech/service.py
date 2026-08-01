"""Serviço de aplicação para registrar entidades e sua proveniência."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .contracts import SchemaRegistry
from .ids import stable_id
from .models import EntityRecord, ProvenanceRecord
from .persistence import JsonlRepository


class StatetechDataService:
    def __init__(self, repository: JsonlRepository, schemas: SchemaRegistry) -> None:
        self.repository = repository
        self.schemas = schemas

    def register_entity(
        self,
        *,
        entity_type: str,
        natural_key: str,
        payload: dict[str, Any],
        provenance: ProvenanceRecord,
        previous_version_id: str | None = None,
    ) -> EntityRecord:
        entity_id = stable_id(entity_type, natural_key)
        schema_record = dict(payload)
        schema_record.setdefault(f"{entity_type}_id", entity_id)
        self.schemas.validate_structure(entity_type, schema_record)

        entity = EntityRecord(
            entity_type=entity_type,
            entity_id=entity_id,
            payload=schema_record,
            previous_version_id=previous_version_id,
        )
        linked_provenance = replace(
            provenance,
            entity_type=entity_type,
            entity_id=entity_id,
            version_id=entity.version_id,
            output_record_ids=tuple(dict.fromkeys((*provenance.output_record_ids, entity.version_id))),
        )

        self.repository.append("entities", entity.to_dict())
        self.repository.append("provenance", linked_provenance.to_dict())
        return entity
