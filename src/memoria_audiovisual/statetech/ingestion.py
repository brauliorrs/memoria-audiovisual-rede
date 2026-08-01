"""Coordenação entre adaptadores de fonte e o serviço central de dados.

O coordenador oferece pré-visualização validada, preservação opcional da entrada
bruta e commit retomável. Adaptadores continuam sem acesso direto ao ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Literal

from .adapters import AdaptedRecord, SourceAdapter, validate_adapter
from .ingestion_batches import BatchManifest, BatchManifestStore
from .models import EntityRecord, utc_now_iso
from .raw_artifacts import RawArtifactStore
from .service import DigitalInfrastructureDataService

IngestionMode = Literal["preview", "commit"]
ItemStatus = Literal["validated", "committed", "already_committed"]


@dataclass(frozen=True, slots=True)
class IngestionItem:
    position: int
    entity_type: str
    natural_key: str
    payload: dict[str, Any]
    evidence_count: int
    referenced_entity_ids: tuple[str, ...]
    status: ItemStatus
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
    batch_id: str | None = None
    source_artifact_id: str | None = None

    @property
    def committed_count(self) -> int:
        return sum(item.status == "committed" for item in self.items)

    @property
    def resumed_count(self) -> int:
        return sum(item.status == "already_committed" for item in self.items)


class IngestionCoordinator:
    """Valida registros adaptados e controla a passagem ao serviço central."""

    def __init__(
        self,
        service: DigitalInfrastructureDataService,
        *,
        artifact_store: RawArtifactStore | None = None,
        batch_store: BatchManifestStore | None = None,
    ) -> None:
        if (artifact_store is None) != (batch_store is None):
            raise ValueError("artifact_store e batch_store devem ser configurados juntos")
        self.service = service
        self.artifact_store = artifact_store
        self.batch_store = batch_store

    def preview(self, adapter: SourceAdapter, source: Any) -> IngestionResult:
        """Adapta e valida todos os registros sem modificar o ledger."""
        validate_adapter(adapter)
        records = adapter.adapt(source)
        self._validate_batch(records)
        artifact_id, batch_id = self._prepare_identity(adapter, source)
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
            batch_id=batch_id,
            source_artifact_id=artifact_id,
        )

    def commit(self, adapter: SourceAdapter, source: Any) -> IngestionResult:
        """Persiste um lote pré-validado com retomada por chave natural.

        Quando os stores estão configurados, a entrada bruta é preservada antes
        do commit e o manifesto registra cada chave concluída. Uma nova chamada
        com o mesmo conteúdo e a mesma versão do adaptador retoma o mesmo lote.
        """
        validate_adapter(adapter)
        records = adapter.adapt(source)
        self._validate_batch(records)
        artifact_id, batch_id = self._prepare_identity(adapter, source)

        previous = self.batch_store.latest(batch_id) if self.batch_store and batch_id else None
        committed_keys = set(previous.committed_keys if previous else ())
        if self.batch_store and batch_id and artifact_id:
            self.batch_store.append(
                BatchManifest(
                    batch_id=batch_id,
                    adapter_name=adapter.adapter_name,
                    adapter_version=adapter.adapter_version,
                    source_artifact_id=artifact_id,
                    record_count=len(records),
                    status="running",
                    committed_keys=tuple(sorted(committed_keys)),
                    created_at=previous.created_at if previous else utc_now_iso(),
                )
            )

        items: list[IngestionItem] = []
        try:
            for position, original in enumerate(records, start=1):
                record_key = self._record_key(original)
                if record_key in committed_keys:
                    items.append(self._item(position, original, status="already_committed"))
                    continue

                record = self._link_artifact(original, artifact_id)
                entity = self._commit_record(record)
                committed_keys.add(record_key)
                items.append(
                    self._item(
                        position,
                        record,
                        status="committed",
                        entity=entity,
                    )
                )
                self._append_progress(
                    adapter=adapter,
                    batch_id=batch_id,
                    artifact_id=artifact_id,
                    record_count=len(records),
                    committed_keys=committed_keys,
                    status="running",
                    previous=previous,
                )
        except Exception as exc:
            self._append_progress(
                adapter=adapter,
                batch_id=batch_id,
                artifact_id=artifact_id,
                record_count=len(records),
                committed_keys=committed_keys,
                status="failed",
                previous=previous,
                error=str(exc),
            )
            raise

        self._append_progress(
            adapter=adapter,
            batch_id=batch_id,
            artifact_id=artifact_id,
            record_count=len(records),
            committed_keys=committed_keys,
            status="completed",
            previous=previous,
        )
        return IngestionResult(
            mode="commit",
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
            source_count=1,
            record_count=len(records),
            items=tuple(items),
            batch_id=batch_id,
            source_artifact_id=artifact_id,
        )

    def _prepare_identity(
        self, adapter: SourceAdapter, source: Any
    ) -> tuple[str | None, str | None]:
        if self.artifact_store is None or self.batch_store is None:
            return None, None
        artifact = self.artifact_store.preserve(source)
        batch_id = self.batch_store.build_batch_id(
            adapter_name=adapter.adapter_name,
            adapter_version=adapter.adapter_version,
            source_artifact_id=artifact.artifact_id,
        )
        return artifact.artifact_id, batch_id

    @staticmethod
    def _record_key(record: AdaptedRecord) -> str:
        return f"{record.entity_type}:{record.natural_key}"

    @staticmethod
    def _link_artifact(record: AdaptedRecord, artifact_id: str | None) -> AdaptedRecord:
        if artifact_id is None:
            return record
        provenance = replace(
            record.provenance,
            input_artifact_ids=tuple(
                dict.fromkeys((*record.provenance.input_artifact_ids, artifact_id))
            ),
        )
        return replace(record, provenance=provenance)

    @staticmethod
    def _item(
        position: int,
        record: AdaptedRecord,
        *,
        status: ItemStatus,
        entity: EntityRecord | None = None,
    ) -> IngestionItem:
        return IngestionItem(
            position=position,
            entity_type=record.entity_type,
            natural_key=record.natural_key,
            payload=dict(record.payload),
            evidence_count=len(record.evidences),
            referenced_entity_ids=record.referenced_entity_ids,
            status=status,
            entity_id=entity.entity_id if entity else None,
            version_id=entity.version_id if entity else None,
        )

    def _append_progress(
        self,
        *,
        adapter: SourceAdapter,
        batch_id: str | None,
        artifact_id: str | None,
        record_count: int,
        committed_keys: set[str],
        status: Literal["running", "completed", "failed"],
        previous: BatchManifest | None,
        error: str | None = None,
    ) -> None:
        if self.batch_store is None or batch_id is None or artifact_id is None:
            return
        self.batch_store.append(
            BatchManifest(
                batch_id=batch_id,
                adapter_name=adapter.adapter_name,
                adapter_version=adapter.adapter_version,
                source_artifact_id=artifact_id,
                record_count=record_count,
                status=status,
                committed_keys=tuple(sorted(committed_keys)),
                created_at=previous.created_at if previous else utc_now_iso(),
                updated_at=utc_now_iso(),
                error=error,
            )
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
