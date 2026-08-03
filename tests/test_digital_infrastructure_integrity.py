from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.integrity import (
    IntegrityError,
    IntegrityValidator,
    LedgerIndex,
)
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger


class IntegrityTests(unittest.TestCase):
    def test_index_rebuilds_entities_versions_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(
                [
                    {
                        "record_type": "entity_version",
                        "payload": {
                            "entity_id": "institution_x",
                            "version_id": "version_1",
                        },
                    },
                    {
                        "record_type": "evidence",
                        "payload": {"evidence_id": "evidence_1"},
                    },
                ]
            )
            index = LedgerIndex.build(ledger)
            self.assertIn("institution_x", index.entities)
            self.assertIn("version_1", index.versions)
            self.assertIn("evidence_1", index.evidences)
            self.assertEqual(index.latest_version_by_entity["institution_x"], "version_1")

    def test_existing_entity_requires_latest_previous_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(
                [
                    {
                        "record_type": "entity_version",
                        "payload": {
                            "entity_id": "institution_x",
                            "version_id": "version_1",
                        },
                    }
                ]
            )
            validator = IntegrityValidator(ledger)
            with self.assertRaises(IntegrityError):
                validator.validate_entity_version(
                    entity_id="institution_x",
                    version_id="version_2",
                    previous_version_id=None,
                )
            validator.validate_entity_version(
                entity_id="institution_x",
                version_id="version_2",
                previous_version_id="version_1",
            )

    def test_orphan_reference_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator = IntegrityValidator(AtomicLedger(Path(tmp) / "ledger.jsonl"))
            with self.assertRaises(IntegrityError):
                validator.validate_entity_references(("provider_missing",))

    def test_pending_evidence_is_valid_inside_same_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator = IntegrityValidator(AtomicLedger(Path(tmp) / "ledger.jsonl"))
            validator.validate_evidence_references(
                ("evidence_new",), pending_evidence_ids=("evidence_new",)
            )

    def test_duplicate_evidence_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            validator = IntegrityValidator(AtomicLedger(Path(tmp) / "ledger.jsonl"))
            with self.assertRaises(IntegrityError):
                validator.validate_evidence_ids(("evidence_1", "evidence_1"))


if __name__ == "__main__":
    unittest.main()
