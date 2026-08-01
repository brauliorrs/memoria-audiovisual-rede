from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.statetech.audit import LedgerAuditor
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.recovery import LedgerRecovery
from memoria_audiovisual.statetech.resolution import EntityResolver, normalize_label


class ResolutionTests(unittest.TestCase):
    def test_normalize_label_removes_accents_and_punctuation(self) -> None:
        self.assertEqual(normalize_label("Cinémathèque Française"), "cinematheque francaise")

    def test_alias_resolution_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            resolver = EntityResolver(ledger)
            resolver.register_alias(
                entity_type="institution",
                entity_id="institution_cinematheque",
                alias="Cinémathèque Française",
                source="curatorial_review",
                reviewed_by="researcher_1",
            )
            self.assertEqual(
                resolver.resolve("institution", "Cinematheque Francaise"),
                "institution_cinematheque",
            )

    def test_conflicting_alias_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            resolver = EntityResolver(ledger)
            resolver.register_alias(
                entity_type="provider",
                entity_id="provider_a",
                alias="Example Tech",
                source="manual",
                reviewed_by="r1",
            )
            with self.assertRaises(ValueError):
                resolver.register_alias(
                    entity_type="provider",
                    entity_id="provider_b",
                    alias="Example Tech",
                    source="manual",
                    reviewed_by="r2",
                )


class AuditAndRecoveryTests(unittest.TestCase):
    def test_auditor_detects_duplicate_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = AtomicLedger(Path(tmp) / "ledger.jsonl")
            envelope = {
                "record_type": "entity_version",
                "payload": {
                    "entity_id": "institution_x",
                    "version_id": "version_x",
                    "previous_version_id": None,
                },
            }
            ledger.append([envelope])
            ledger.append([envelope])
            issues = LedgerAuditor(ledger).audit()
            self.assertTrue(any(issue.rule_code == "VER-001" for issue in issues))

    def test_recovery_repairs_only_truncated_tail_and_keeps_backup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            path.write_text(
                '{"transaction_id":"txn_1","records":[]}\n{"transaction_id":',
                encoding="utf-8",
            )
            recovery = LedgerRecovery(path)
            report = recovery.repair_truncated_tail()
            self.assertTrue(report.repaired)
            self.assertEqual(report.valid_lines, 1)
            self.assertTrue(Path(str(path) + ".bak").exists())


if __name__ == "__main__":
    unittest.main()
