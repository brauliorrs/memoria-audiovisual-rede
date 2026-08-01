from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.statetech.ids import stable_id, version_id
from memoria_audiovisual.statetech.models import EntityRecord, ProvenanceRecord
from memoria_audiovisual.statetech.persistence import JsonlRepository


class StableIdTests(unittest.TestCase):
    def test_stable_id_is_deterministic(self) -> None:
        first = stable_id("institution", "Arquivo Nacional")
        second = stable_id("institution", "Arquivo Nacional")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("institution_arquivo-nacional_"))

    def test_version_changes_with_payload(self) -> None:
        self.assertNotEqual(
            version_id("institution_x", {"name": "A"}),
            version_id("institution_x", {"name": "B"}),
        )


class ModelAndPersistenceTests(unittest.TestCase):
    def test_entity_version_is_stable(self) -> None:
        record = EntityRecord(
            entity_type="institution",
            entity_id="institution_x",
            payload={"institution_id": "institution_x", "institution_name": "X"},
        )
        self.assertEqual(record.version_id, record.version_id)

    def test_jsonl_repository_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repository = JsonlRepository(Path(tmp))
            repository.append("entities", {"entity_id": "x", "version": 1})
            repository.append("entities", {"entity_id": "x", "version": 2})
            records = repository.read_all("entities")
            self.assertEqual([item["version"] for item in records], [1, 2])
            self.assertEqual(repository.latest_by("entities", "entity_id")["x"]["version"], 2)

    def test_provenance_serializes_tuples_as_lists(self) -> None:
        record = ProvenanceRecord(
            provenance_id="prov_x",
            entity_type="institution",
            entity_id="institution_x",
            activity_type="acquisition",
            agent_type="script",
            source_ids=("source_1",),
        )
        self.assertEqual(record.to_dict()["source_ids"], ["source_1"])


if __name__ == "__main__":
    unittest.main()
