"""Regras executáveis de integridade para o núcleo infraestrutura digital."""

from __future__ import annotations

from dataclasses import dataclass

from .ledger import AtomicLedger


class IntegrityError(ValueError):
    """Indica violação que impede a gravação de uma transação."""


@dataclass(frozen=True, slots=True)
class LedgerIndex:
    entities: frozenset[str]
    versions: frozenset[str]
    evidences: frozenset[str]
    latest_version_by_entity: dict[str, str]

    @classmethod
    def build(cls, ledger: AtomicLedger) -> "LedgerIndex":
        entities: set[str] = set()
        versions: set[str] = set()
        evidences: set[str] = set()
        latest: dict[str, str] = {}

        for entry in ledger.read_all():
            for envelope in entry.records:
                record_type = envelope.get("record_type")
                payload = envelope.get("payload", {})
                if record_type == "entity_version":
                    entity_id = str(payload["entity_id"])
                    version_id = str(payload["version_id"])
                    entities.add(entity_id)
                    versions.add(version_id)
                    latest[entity_id] = version_id
                elif record_type == "evidence":
                    evidences.add(str(payload["evidence_id"]))

        return cls(
            entities=frozenset(entities),
            versions=frozenset(versions),
            evidences=frozenset(evidences),
            latest_version_by_entity=latest,
        )


class IntegrityValidator:
    """Valida duplicidades, versões e referências antes do commit."""

    def __init__(self, ledger: AtomicLedger) -> None:
        self.ledger = ledger

    def validate_entity_version(
        self,
        *,
        entity_id: str,
        version_id: str,
        previous_version_id: str | None,
    ) -> None:
        index = LedgerIndex.build(self.ledger)
        if version_id in index.versions:
            raise IntegrityError(f"versão duplicada: {version_id}")

        latest = index.latest_version_by_entity.get(entity_id)
        if latest is None:
            if previous_version_id is not None:
                raise IntegrityError("primeira versão não pode apontar para versão anterior")
            return

        if previous_version_id is None:
            raise IntegrityError(f"entidade existente exige previous_version_id={latest}")
        if previous_version_id != latest:
            raise IntegrityError(
                f"cadeia de versões inválida: esperado {latest}, recebido {previous_version_id}"
            )

    def validate_evidence_ids(self, evidence_ids: tuple[str, ...]) -> None:
        if len(evidence_ids) != len(set(evidence_ids)):
            raise IntegrityError("evidências duplicadas na mesma transação")

    def validate_entity_references(
        self,
        referenced_entity_ids: tuple[str, ...],
        *,
        pending_entity_ids: tuple[str, ...] = (),
    ) -> None:
        index = LedgerIndex.build(self.ledger)
        available = set(index.entities) | set(pending_entity_ids)
        missing = sorted(set(referenced_entity_ids) - available)
        if missing:
            raise IntegrityError(f"referências órfãs: {', '.join(missing)}")

    def validate_evidence_references(
        self,
        evidence_ids: tuple[str, ...],
        *,
        pending_evidence_ids: tuple[str, ...] = (),
    ) -> None:
        index = LedgerIndex.build(self.ledger)
        available = set(index.evidences) | set(pending_evidence_ids)
        missing = sorted(set(evidence_ids) - available)
        if missing:
            raise IntegrityError(f"evidências não registradas: {', '.join(missing)}")
