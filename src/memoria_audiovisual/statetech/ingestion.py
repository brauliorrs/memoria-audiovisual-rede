"""Coordenação entre adaptadores de fonte e o serviço central de dados.

O coordenador oferece pré-visualização validada sem persistência e commit
controlado. Adaptadores continuam sem acesso direto ao ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from .adapters import AdaptedRecord, SourceAdapter, validate_adapter
from .models import EntityRecord
from .service import StatetechDataService

IngestionMode = Literal["preview", "commit"]


@dataclass(frozen=True, slots=True)
class IngestionItem:
    position: int
    entity_type: str
    natural_key: str
    payload: dict[str, Any]
    evidence_count: int
    referenced_entity_ids: tuple[str, ...]
    status: Literal["validated", "committed"]
    entity_id: str | None = None
    version_id: str | None = None


@dataclass(frozen=True, slots=True)
class IngestionResult:
    mode: IngestionMode
    adapter_name: str
    adapter_version: str
    source_count: int
    record_count: int
    items: tuple[IngestionItem, ...]

    @property
    def committed_count(self) -> int:
        return sum(item.status == "committed" for item in self.items)


class IngestionCoordinator:
    """Valida registros adaptados e controla a passagem ao serviço central."""

    def __init__(self, service: StatetechDataService) -> None:
        self.service = service

    def preview(self, adapter: SourceAdapter, source: Any) -> IngestionResult:
        """Adapta e valida todos os registros sem modificar o ledger."""
        validate_adapter(adapter)
        records = adapter.adapt(source)
        self._validate_batch(records)
        items = tuple(
            IngestionItem(
                position=position,
                entity_type=record.entity_type,
                natural_key=record.natural_key,
                payload=dict(record.payload),
                evidence_count=len(record.evidences),
                referenced_entity_ids=record.referenced_entity_ids,
                status="validated",
            )
            for position, record in enumerate(records, start=1)
        )
        return IngestionResult(
            mode="preview",
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
            source_count=1,
            record_count=len(records),
            items=items,
        )

    def commit(self, adapter: SourceAdapter, source: Any) -> IngestionResult:
        """Valida o lote completo antes de encaminhar registros ao serviço central.

        A pré-validação reduz commits parciais por erro de contrato. A persistência
        continua ocorrendo registro a registro porque o ledger da Fase 1 trabalha
        com uma transação lógica por entidade, evidências e proveniência.
        """
        validate_adapter(adapter)
        records = adapter.adapt(source)
        self._validate_batch(records)

        committed: list[IngestionItem] = []
        for position, record in enumerate(records, start=1):
            entity = self._commit_record(record)
            committed.append(
                IngestionItem(
                    position=position,
                    entity_type=record.entity_type,
                    natural_key=record.natural_key,
                    payload=dict(record.payload),
                    evidence_count=len(record.evidences),
                    referenced_entity_ids=record.referenced_entity_ids,
                    status="committed",
                    entity_id=entity.entity_id,
                    version_id=entity.version_id,
                )
            )
        return IngestionResult(
            mode="commit",
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
            source_count=1,
            record_count=len(records),
            items=tuple(committed),
        )

    def _validate_batch(self, records: tuple[AdaptedRecord, ...]) -> None:
        seen_keys: set[tuple[str, str]] = set()
        for record in records:
            if not record.entity_type.strip():
                raise ValueError("entity_type não pode ser vazio")
            if not record.natural_key.strip():
                raise ValueError("natural_key não pode ser vazio")
            key = (record.entity_type, record.natural_key)
            if key in seen_keys:
                raise ValueError(
                    f"registro adaptado duplicado no lote: {record.entity_type}:{record.natural_key}"
                )
            seen_keys.add(key)
            self.service.validator.validate(record.entity_type, dict(record.payload))

    def _commit_record(self, record: AdaptedRecord) -> EntityRecord:
        return self.service.register_entity(
            entity_type=record.entity_type,
            natural_key=record.natural_key,
            payload=dict(record.payload),
            provenance=record.provenance,
            evidences=record.evidences,
            previous_version_id=record.previous_version_id,
            referenced_entity_ids=record.referenced_entity_ids,
        )
