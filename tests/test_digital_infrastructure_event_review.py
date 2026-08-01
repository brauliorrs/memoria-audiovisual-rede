from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.event_review import (
    LongitudinalEventReview,
    LongitudinalEventReviewService,
)
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger


class LongitudinalEventReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.service = LongitudinalEventReviewService(
            AtomicLedger(Path(self.temporary.name) / "ledger.jsonl")
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def event(triage_class: str = "material_change") -> dict[str, object]:
        return {
            "event_id": "event_1",
            "snapshot_id": "snapshot_2",
            "corpus_code": "ina",
            "detector_group": "technology",
            "change_type": "changed",
            "triage_class": triage_class,
            "review_required": True,
            "publication_status": "pending_review",
        }

    def test_material_change_requires_one_confirmation(self) -> None:
        review = LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="researcher",
            decision="confirmed", justification="Evidência conferida.", evidence_ids=("ev1",),
        )
        self.service.register(review)
        state = self.service.current_state(self.event())
        self.assertEqual(state.current_status, "confirmed")
        self.assertEqual(state.publication_status, "publishable_after_review")

    def test_disappearance_requires_two_distinct_reviewers(self) -> None:
        event = self.event("disappearance_alert")
        self.service.register(LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="researcher",
            decision="confirmed", justification="Primeira conferência.", evidence_ids=("ev1",),
        ))
        self.assertEqual(self.service.current_state(event).current_status, "pending_review")
        self.service.register(LongitudinalEventReview(
            event_id="event_1", reviewer_id="r2", reviewer_role="curator",
            decision="confirmed", justification="Segunda conferência.", evidence_ids=("ev2",),
        ))
        self.assertEqual(self.service.current_state(event).current_status, "confirmed")

    def test_rejection_blocks_publication(self) -> None:
        self.service.register(LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="curator",
            decision="rejected", justification="Mudança causada por falha temporária.", evidence_ids=("ev1",),
        ))
        state = self.service.current_state(self.event())
        self.assertEqual(state.current_status, "rejected")
        self.assertEqual(state.publication_status, "blocked")

    def test_reclassification_requires_valid_class(self) -> None:
        with self.assertRaises(ValueError):
            LongitudinalEventReview(
                event_id="event_1", reviewer_id="r1", reviewer_role="curator",
                decision="reclassified", justification="Reclassificar.", evidence_ids=("ev1",),
                reclassified_as="invalid",
            )

    def test_same_reviewer_must_supersede_previous_decision(self) -> None:
        first = self.service.register(LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="curator",
            decision="needs_evidence", justification="Falta comprovação.",
        ))
        with self.assertRaises(ValueError):
            self.service.register(LongitudinalEventReview(
                event_id="event_1", reviewer_id="r1", reviewer_role="curator",
                decision="confirmed", justification="Agora confirmado.", evidence_ids=("ev1",),
            ))
        second = LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="curator",
            decision="confirmed", justification="Agora confirmado.", evidence_ids=("ev1",),
            supersedes_review_id=first.review_id,
        )
        self.service.register(second)
        self.assertEqual(self.service.current_state(self.event()).current_status, "confirmed")

    def test_queue_excludes_resolved_events(self) -> None:
        self.service.register(LongitudinalEventReview(
            event_id="event_1", reviewer_id="r1", reviewer_role="curator",
            decision="confirmed", justification="Confirmado.", evidence_ids=("ev1",),
        ))
        self.assertEqual(self.service.export_queue((self.event(),)), ())


if __name__ == "__main__":
    unittest.main()
