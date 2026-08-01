from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memoria_audiovisual.statetech.adapters import AdaptedRecord
from memoria_audiovisual.statetech.ingestion import IngestionCoordinator
from memoria_audiovisual.statetech.ingestion_batches import BatchManifestStore
from memoria_audiovisual.statetech.models import EntityRecord, ProvenanceRecord
from memoria_audiovisual.statetech.raw_artifacts import RawArtifactStore


class _Validator:
    def validate(self, entity_type: str, payload: dict[str, Any]) -> None:
        return None


class _Service:
    def __init__(self, *, fail_on: int | None = None) -> None:
        self.validator = _Validator()
        self.registered: list[dict[str, Any]] = []
        self.fail_on = fail_on

    def register_entity(self, **kwargs: Any) -> EntityRecord:
        next_position = len(self.registered) + 1
        if self.fail_on == next_position:
            self.fail_on = None
            raise RuntimeError("falha simulada")
        self.registered.append(kwargs)
        return EntityRecord(
            entity_type=kwargs["entity_type"],
            entity_id=f"entity_{next_position}",
            payload=dict(kwargs["payload"]),
        )


@dataclass
class _Adapter:
    records: tuple[AdaptedRecord, ...]
    adapter_name: str = "artifact_adapter"
    adapter_version: str = "1.0.0"

    def adapt(self, source: Any) -> tuple[AdaptedRecord, ...]:
        return self.records


def _record(key: str) -> AdaptedRecord:
    return AdaptedRecord(
        entity_type="digital_infrastructure_audit",
        natural_key=key,
        payload={"observation_id": key},
        provenance=ProvenanceRecord(
            provenance_id=f"prov_{key}",
            entity_type="digital_infrastructure_audit",
            entity_id=key,
            activity_type="adaptation",
            agent_type="script",
        ),
    )


class IngestionArtifactTests(unittest.TestCase):
    def test_same_source_produces_same_artifact_and_batch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = _Service()
            coordinator = IngestionCoordinator(
                service,  # type: ignore[arg-type]
                artifact_store=RawArtifactStore(Path(directory) / "raw"),
                batch_store=BatchManifestStore(Path(directory) / "batches.jsonl"),
            )
            adapter = _Adapter((_record("a"),))
            source = {"institution": "Example", "reachable": True}

            first = coordinator.preview(adapter, source)
            second = coordinator.preview(adapter, source)

            self.assertEqual(first.source_artifact_id, second.source_artifact_id)
            self.assertEqual(first.batch_id, second.batch_id)
            self.assertTrue(first.source_artifact_id)

    def test_commit_links_raw_artifact_to_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = _Service()
            coordinator = IngestionCoordinator(
                service,  # type: ignore[arg-type]
                artifact_store=RawArtifactStore(Path(directory) / "raw"),
                batch_store=BatchManifestStore(Path(directory) / "batches.jsonl"),
            )

            result = coordinator.commit(_Adapter((_record("a"),)), {"raw": 1})

            provenance = service.registered[0]["provenance"]
            self.assertIn(result.source_artifact_id, provenance.input_artifact_ids)
            self.assertEqual(result.committed_count, 1)

    def test_interrupted_batch_resumes_without_recommitting_finished_keys(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = _Service(fail_on=2)
            coordinator = IngestionCoordinator(
                service,  # type: ignore[arg-type]
                artifact_store=RawArtifactStore(Path(directory) / "raw"),
                batch_store=BatchManifestStore(Path(directory) / "batches.jsonl"),
            )
            adapter = _Adapter((_record("a"), _record("b"), _record("c")))
            source = {"raw": "same"}

            with self.assertRaises(RuntimeError):
                coordinator.commit(adapter, source)
            self.assertEqual(len(service.registered), 1)

            resumed = coordinator.commit(adapter, source)

            self.assertEqual(resumed.resumed_count, 1)
            self.assertEqual(resumed.committed_count, 2)
            self.assertEqual(len(service.registered), 3)


if __name__ == "__main__":
    unittest.main()
