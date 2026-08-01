from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.curatorial_review import CuratorialReview, CuratorialReviewService
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.review_files import export_review_queue, import_review_decisions


class ReviewFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.service = CuratorialReviewService(AtomicLedger(self.root / "ledger.jsonl"))
        self.observation = {
            "observation_id": "obs_1",
            "corpus_code": "archive",
            "institution_name": "Archive",
            "detector_group": "ai_evidence",
            "detected_value": "reconhecimento facial",
            "automatic_confidence": "low",
            "evidence_url": "https://example.org",
            "detection_status": "detected",
            "review_status": "pending_review",
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_sensitive_queue_requires_two_confirmations(self) -> None:
        queue = self.service.export_queue((self.observation,))
        self.assertTrue(queue[0].sensitive)
        self.assertEqual(queue[0].required_confirmations, 2)

    def test_sensitive_observation_needs_two_distinct_reviewers(self) -> None:
        first = CuratorialReview(
            observation_id="obs_1", reviewer_id="r1", reviewer_role="curator_reviewer",
            decision="confirmed", justification="evidência conferida", evidence_ids=("ev1",),
        )
        self.service.register(first)
        self.assertIsNone(self.service.approved_for_materialization(self.observation))
        second = CuratorialReview(
            observation_id="obs_1", reviewer_id="r2", reviewer_role="senior_curator",
            decision="confirmed", justification="segunda conferência", evidence_ids=("ev1",),
            supersedes_review_id=first.review_id,
        )
        self.service.register(second)
        self.assertIsNotNone(self.service.approved_for_materialization(self.observation))

    def test_export_json_and_import_decisions(self) -> None:
        queue_path = export_review_queue(self.service, (self.observation,), self.root / "queue.json")
        self.assertEqual(len(json.loads(queue_path.read_text(encoding="utf-8"))), 1)
        decisions = [{
            "observation_id": "obs_1", "reviewer_id": "r1",
            "reviewer_role": "curator_reviewer", "decision": "confirmed",
            "justification": "fonte verificada", "evidence_ids": ["ev1"],
        }]
        input_path = self.root / "decisions.json"
        input_path.write_text(json.dumps(decisions), encoding="utf-8")
        imported = import_review_decisions(self.service, input_path)
        self.assertEqual(len(imported), 1)
        self.assertEqual(self.service.latest("obs_1").reviewer_id, "r1")


if __name__ == "__main__":
    unittest.main()
