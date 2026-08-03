from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from memoria_audiovisual.digital_infrastructure.adapters import AdaptedRecord
from memoria_audiovisual.digital_infrastructure.ingestion import IngestionCoordinator
from memoria_audiovisual.digital_infrastructure.models import EntityRecord, ProvenanceRecord


class _Validator:
    def __init__(self) -> None:
        self.validated: list[tuple[str, dict[str, Any]]] = []

    def validate(self, entity_type: str, payload: dict[str, Any]) -> None:
        if payload.get("invalid"):
            raise ValueError("payload inválido")
        self.validated.append((entity_type, payload))


class _Service:
    def __init__(self) -> None:
        self.validator = _Validator()
        self.registered: list[dict[str, Any]] = []

    def register_entity(self, **kwargs: Any) -> EntityRecord:
        self.registered.append(kwargs)
        return EntityRecord(
            entity_type=kwargs["entity_type"],
            entity_id=f"entity_{len(self.registered)}",
            payload=dict(kwargs["payload"]),
            previous_version_id=kwargs.get("previous_version_id"),
        )


@dataclass
class _Adapter:
    records: tuple[AdaptedRecord, ...]
    adapter_name: str = "test_adapter"
    adapter_version: str = "1.0.0"

    def adapt(self, source: Any) -> tuple[AdaptedRecord, ...]:
        return self.records


def _record(natural_key: str, *, invalid: bool = False) -> AdaptedRecord:
    return AdaptedRecord(
        entity_type="digital_infrastructure_audit",
        natural_key=natural_key,
        payload={"observation_id": natural_key, "invalid": invalid},
        provenance=ProvenanceRecord(
            provenance_id=f"prov_{natural_key}",
            entity_type="digital_infrastructure_audit",
            entity_id=natural_key,
            activity_type="adaptation",
            agent_type="script",
        ),
    )


class IngestionCoordinatorTests(unittest.TestCase):
    def test_preview_validates_without_persisting(self) -> None:
        service = _Service()
        coordinator = IngestionCoordinator(service)  # type: ignore[arg-type]
        result = coordinator.preview(_Adapter((_record("a"), _record("b"))), source={})

        self.assertEqual(result.mode, "preview")
        self.assertEqual(result.record_count, 2)
        self.assertEqual(result.committed_count, 0)
        self.assertEqual(len(service.validator.validated), 2)
        self.assertEqual(service.registered, [])

    def test_commit_prevalidates_and_persists_records(self) -> None:
        service = _Service()
        coordinator = IngestionCoordinator(service)  # type: ignore[arg-type]
        result = coordinator.commit(_Adapter((_record("a"), _record("b"))), source={})

        self.assertEqual(result.mode, "commit")
        self.assertEqual(result.committed_count, 2)
        self.assertEqual(len(service.registered), 2)
        self.assertTrue(all(item.entity_id for item in result.items))
        self.assertTrue(all(item.version_id for item in result.items))

    def test_invalid_batch_does_not_start_persistence(self) -> None:
        service = _Service()
        coordinator = IngestionCoordinator(service)  # type: ignore[arg-type]

        with self.assertRaises(ValueError):
            coordinator.commit(_Adapter((_record("a"), _record("b", invalid=True))), source={})

        self.assertEqual(service.registered, [])

    def test_duplicate_natural_key_is_rejected(self) -> None:
        service = _Service()
        coordinator = IngestionCoordinator(service)  # type: ignore[arg-type]

        with self.assertRaisesRegex(ValueError, "duplicado"):
            coordinator.preview(_Adapter((_record("same"), _record("same"))), source={})


if __name__ == "__main__":
    unittest.main()
