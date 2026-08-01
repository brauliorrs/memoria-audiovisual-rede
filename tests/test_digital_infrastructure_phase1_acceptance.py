from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.audit import LedgerAuditor
from memoria_audiovisual.digital_infrastructure.contracts import SchemaRegistry
from memoria_audiovisual.digital_infrastructure.entity_decisions import EntityDecision
from memoria_audiovisual.digital_infrastructure.index_store import (
    verify_index_snapshot,
    write_index_snapshot,
)
from memoria_audiovisual.digital_infrastructure.integrity import IntegrityError
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.reporting import export_integrity_report
from memoria_audiovisual.digital_infrastructure.service import DigitalInfrastructureDataService


class Phase1AcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository_root = Path(__file__).resolve().parents[1]
        self.schemas = SchemaRegistry(self.repository_root)

    def test_entity_decision_is_validated_and_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(
                (
                    {
                        "record_type": "entity_version",
                        "payload": {
                            "entity_type": "institution",
                            "entity_id": "institution_a",
                            "version_id": "version_a",
                            "payload": {},
                            "validation_status": "confirmed",
                            "recorded_at": "2026-08-01T12:00:00+00:00",
                            "schema_version": "1.0.0",
                            "previous_version_id": None,
                        },
                    },
                    {
                        "record_type": "entity_version",
                        "payload": {
                            "entity_type": "institution",
                            "entity_id": "institution_b",
                            "version_id": "version_b",
                            "payload": {},
                            "validation_status": "confirmed",
                            "recorded_at": "2026-08-01T12:00:00+00:00",
                            "schema_version": "1.0.0",
                            "previous_version_id": None,
                        },
                    },
                )
            )
            service = DigitalInfrastructureDataService(ledger, self.schemas)
            result = service.register_entity_decision(
                EntityDecision(
                    decision_type="redirect",
                    source_entity_ids=("institution_a",),
                    target_entity_ids=("institution_b",),
                    rationale="Identidade institucional confirmada por revisão curatorial.",
                    decided_by="reviewer_1",
                    status="approved",
                    decided_at="2026-08-01T12:30:00+00:00",
                )
            )
            self.assertTrue(result["decision_id"])
            self.assertEqual(ledger.read_all()[-1].records[0]["record_type"], "entity_decision")

    def test_entity_decision_rejects_orphan_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            service = DigitalInfrastructureDataService(ledger, self.schemas)
            with self.assertRaises(IntegrityError):
                service.register_entity_decision(
                    EntityDecision(
                        decision_type="redirect",
                        source_entity_ids=("missing_a",),
                        target_entity_ids=("missing_b",),
                        rationale="Teste de referência órfã.",
                        decided_by="reviewer_1",
                        status="approved",
                    )
                )

    def test_integrity_report_matches_registered_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            destination = Path(tmp) / "integrity_report.json"
            export_integrity_report(LedgerAuditor(ledger), destination, self.schemas)
            report = json.loads(destination.read_text(encoding="utf-8"))
            self.assertEqual(report["status"], "passed")
            self.assertEqual(report["summary"]["records_checked"], 0)

    def test_derived_index_can_be_written_and_verified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(
                (
                    {
                        "record_type": "evidence",
                        "payload": {"evidence_id": "evidence_a"},
                    },
                )
            )
            index_path = write_index_snapshot(ledger, Path(tmp) / "index.json")
            self.assertTrue(verify_index_snapshot(ledger, index_path))
            ledger.append(
                (
                    {
                        "record_type": "evidence",
                        "payload": {"evidence_id": "evidence_b"},
                    },
                )
            )
            self.assertFalse(verify_index_snapshot(ledger, index_path))


if __name__ == "__main__":
    unittest.main()
