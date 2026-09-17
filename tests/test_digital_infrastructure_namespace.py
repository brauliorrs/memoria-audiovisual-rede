from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.contracts import SchemaRegistry
from memoria_audiovisual.digital_infrastructure.evidence import EvidenceRecord
from memoria_audiovisual.digital_infrastructure.ids import stable_id
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.models import EntityRecord
from memoria_audiovisual.digital_infrastructure.service import DigitalInfrastructureDataService
from memoria_audiovisual.statetech.contracts import SchemaRegistry as LegacySchemaRegistry
from memoria_audiovisual.statetech.evidence import EvidenceRecord as LegacyEvidenceRecord
from memoria_audiovisual.statetech.ids import stable_id as legacy_stable_id
from memoria_audiovisual.statetech.ledger import AtomicLedger as LegacyAtomicLedger
from memoria_audiovisual.statetech.models import EntityRecord as LegacyEntityRecord
from memoria_audiovisual.statetech.service import StatetechDataService


class DigitalInfrastructureNamespaceTests(unittest.TestCase):
    def test_historical_stable_ids_do_not_change_with_python_namespace(self) -> None:
        expected = "institution_arquivo-nacional_6fd1d17528a7"
        self.assertEqual(stable_id("institution", "Arquivo Nacional"), expected)
        self.assertEqual(legacy_stable_id("institution", "Arquivo Nacional"), expected)
        self.assertEqual(
            stable_id("institution", "Arquivo Nacional"),
            stable_id("institution", "Arquivo Nacional", namespace="statetech"),
        )
        self.assertNotEqual(
            stable_id("institution", "Arquivo Nacional"),
            stable_id("institution", "Arquivo Nacional", namespace="digital_infrastructure"),
        )

    def test_legacy_imports_resolve_to_canonical_core_objects(self) -> None:
        self.assertIs(LegacyEntityRecord, EntityRecord)
        self.assertIs(LegacyEvidenceRecord, EvidenceRecord)
        self.assertIs(LegacyAtomicLedger, AtomicLedger)
        self.assertIs(LegacySchemaRegistry, SchemaRegistry)
        self.assertIs(StatetechDataService, DigitalInfrastructureDataService)

    def test_evidence_url_remains_part_of_evidence_identity(self) -> None:
        common = {
            "evidence_type": "official_page",
            "collection_method": "manual_review",
            "observation_date": "2026-09-01T00:00:00+00:00",
        }
        first = EvidenceRecord(evidence_url="https://one.example", **common).to_dict()
        second = EvidenceRecord(evidence_url="https://two.example", **common).to_dict()
        self.assertNotEqual(first["evidence_id"], second["evidence_id"])
        self.assertEqual(first["validation_status"], "pending_review")
        self.assertEqual(second["validation_status"], "pending_review")

    def test_append_only_ledger_is_interoperable_between_namespaces(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            AtomicLedger(path).append(({"record_type": "evidence", "payload": {"evidence_id": "e1"}},))
            LegacyAtomicLedger(path).append(({"record_type": "evidence", "payload": {"evidence_id": "e2"}},))
            entries = AtomicLedger(path).read_all()
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0].records[0]["payload"]["evidence_id"], "e1")
            self.assertEqual(entries[1].records[0]["payload"]["evidence_id"], "e2")

    def test_schema_registry_keeps_historical_contract_location(self) -> None:
        root = Path(__file__).resolve().parents[1]
        registry = SchemaRegistry(root)
        self.assertTrue(registry.schema_version)
        self.assertIn("institution", registry.paths)

    def test_entity_default_remains_pending_review(self) -> None:
        entity = EntityRecord(entity_type="institution", entity_id="institution_x", payload={})
        self.assertEqual(entity.validation_status, "pending_review")


if __name__ == "__main__":
    unittest.main()
