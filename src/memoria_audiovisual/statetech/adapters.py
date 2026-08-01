"""Contratos de entrada para futuros adaptadores da Fase 2."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from .evidence import EvidenceRecord
from .models import ProvenanceRecord


@dataclass(frozen=True, slots=True)
class AdaptedRecord:
    entity_type: str
    natural_key: str
    payload: dict[str, Any]
    provenance: ProvenanceRecord
    evidences: tuple[EvidenceRecord, ...] = ()
    referenced_entity_ids: tuple[str, ...] = ()
    previous_version_id: str | None = None


@runtime_checkable
class SourceAdapter(Protocol):
    """Interface mínima para transformar uma fonte externa no contrato interno."""

    adapter_name: str
    adapter_version: str

    def adapt(self, source: Any) -> tuple[AdaptedRecord, ...]:
        """Transforma entrada externa sem persistir ou publicar dados."""
        ...


def validate_adapter(adapter: SourceAdapter) -> None:
    if not adapter.adapter_name.strip():
        raise ValueError("adapter_name não pode ser vazio")
    if not adapter.adapter_version.strip():
        raise ValueError("adapter_version não pode ser vazio")
    if not callable(getattr(adapter, "adapt", None)):
        raise TypeError("o adaptador deve implementar adapt(source)")
