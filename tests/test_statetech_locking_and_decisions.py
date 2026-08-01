from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.statetech.entity_decisions import EntityDecision, build_redirect_map
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.locking import FileWriteLock, LedgerLockTimeout


class LockingTests(unittest.TestCase):
    def test_lock_blocks_second_writer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "ledger.jsonl"
            with FileWriteLock(target, timeout=0.1, poll_interval=0.01):
                with self.assertRaises(LedgerLockTimeout):
                    FileWriteLock(target, timeout=0.02, poll_interval=0.005).acquire()

    def test_ledger_removes_lock_after_append(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "ledger.jsonl"
            AtomicLedger(target).append(({"record_type": "test", "payload": {"id": "x"}},))
            self.assertFalse(Path(f"{target}.lock").exists())


class EntityDecisionTests(unittest.TestCase):
    def test_approved_redirect_builds_map(self) -> None:
        decision = EntityDecision(
            decision_type="redirect",
            source_entity_ids=("institution_old",),
            target_entity_ids=("institution_new",),
            rationale="nome institucional atualizado",
            decided_by="reviewer_1",
            status="approved",
        )
        self.assertEqual(build_redirect_map((decision,)), {"institution_old": "institution_new"})

    def test_split_requires_multiple_targets(self) -> None:
        decision = EntityDecision(
            decision_type="split",
            source_entity_ids=("institution_x",),
            target_entity_ids=("institution_a",),
            rationale="unidade composta",
            decided_by="reviewer_1",
        )
        with self.assertRaises(ValueError):
            decision.to_dict()

    def test_conflicting_redirects_are_rejected(self) -> None:
        first = EntityDecision(
            decision_type="redirect",
            source_entity_ids=("institution_x",),
            target_entity_ids=("institution_a",),
            rationale="primeira decisão",
            decided_by="reviewer_1",
            status="approved",
        )
        second = EntityDecision(
            decision_type="merge",
            source_entity_ids=("institution_x",),
            target_entity_ids=("institution_b",),
            rationale="decisão conflitante",
            decided_by="reviewer_2",
            status="approved",
        )
        with self.assertRaises(ValueError):
            build_redirect_map((first, second))


if __name__ == "__main__":
    unittest.main()
