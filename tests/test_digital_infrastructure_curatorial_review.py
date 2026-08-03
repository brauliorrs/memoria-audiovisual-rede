from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.curatorial_review import (
    CuratorialReview,
    CuratorialReviewService,
)
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger


class CuratorialReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        ledger = AtomicLedger(Path(self.tempdir.name) / "ledger.jsonl")
        self.service = CuratorialReviewService(ledger)
        self.observation = {
            "observation_id": "obs_1",
            "corpus_code": "archive",
            "institution_name": "Archive",
            "detector_group": "api_service",
            "detected_value": "IIIF",
            "detection_status": "detected",
            "automatic_confidence": "medium",
            "evidence_url": "https://example.org/iiif",
            "review_status": "pending_review",
        }

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_confirmed_review_is_append_only_and_applied(self) -> None:
        review = CuratorialReview(
            observation_id="obs_1",
            reviewer_id="reviewer_a",
            reviewer_role="curator_reviewer",
            decision="confirmed",
            justification="Manifesto IIIF verificado manualmente.",
            evidence_ids=("evidence_1",),
            reviewed_at="2026-08-01T18:00:00+00:00",
        )
        self.service.register(review)

        reviewed = self.service.apply_latest(self.observation)
        self.assertEqual(reviewed["review_status"], "confirmed")
        self.assertEqual(reviewed["reviewer"], "reviewer_a")
        self.assertEqual(reviewed["curatorial_review_id"], review.review_id)
        self.assertIsNotNone(self.service.approved_for_materialization(self.observation))

    def test_second_review_must_supersede_latest(self) -> None:
        first = self.service.register(CuratorialReview(
            observation_id="obs_1",
            reviewer_id="reviewer_a",
            reviewer_role="curator_reviewer",
            decision="confirmed",
            justification="Primeira análise.",
            evidence_ids=("evidence_1",),
            reviewed_at="2026-08-01T18:00:00+00:00",
        ))
        with self.assertRaisesRegex(ValueError, "substituir explicitamente"):
            self.service.register(CuratorialReview(
                observation_id="obs_1",
                reviewer_id="reviewer_b",
                reviewer_role="senior_curator",
                decision="false_positive",
                justification="Revisão sênior identificou falso positivo.",
                evidence_ids=("evidence_2",),
                reviewed_at="2026-08-01T19:00:00+00:00",
            ))

        second = CuratorialReview(
            observation_id="obs_1",
            reviewer_id="reviewer_b",
            reviewer_role="senior_curator",
            decision="false_positive",
            justification="Revisão sênior identificou falso positivo.",
            evidence_ids=("evidence_2",),
            reviewed_at="2026-08-01T19:00:00+00:00",
            supersedes_review_id=first.review_id,
        )
        self.service.register(second)
        self.assertEqual(self.service.latest("obs_1").decision, "false_positive")
        self.assertIsNone(self.service.approved_for_materialization(self.observation))

    def test_queue_excludes_reviewed_by_default(self) -> None:
        other = dict(self.observation, observation_id="obs_2")
        self.service.register(CuratorialReview(
            observation_id="obs_1",
            reviewer_id="reviewer_a",
            reviewer_role="curator_reviewer",
            decision="inconclusive",
            justification="Evidência insuficiente.",
            evidence_ids=(),
            reviewed_at="2026-08-01T18:00:00+00:00",
        ))
        queue = self.service.export_queue((self.observation, other))
        self.assertEqual([item.observation_id for item in queue], ["obs_2"])

    def test_confirmed_decision_requires_evidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "evidência"):
            CuratorialReview(
                observation_id="obs_1",
                reviewer_id="reviewer_a",
                reviewer_role="curator_reviewer",
                decision="confirmed",
                justification="Sem evidência.",
                evidence_ids=(),
            )


if __name__ == "__main__":
    unittest.main()
