from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.event_review import (
    LongitudinalEventReview,
    LongitudinalEventReviewService,
)
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.public_view import PublicEvent
from memoria_audiovisual.digital_infrastructure.publication_revision import (
    PublicationRevisionStore,
    regenerate_publication,
)


class PublicationRevisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name) / "public"
        self.snapshot_id = "snapshot_2026_09"
        snapshot = self.root / self.snapshot_id
        snapshot.mkdir(parents=True)
        initial = PublicEvent(
            event_id="routine_1",
            snapshot_id=self.snapshot_id,
            corpus_code="ina",
            detector_group="technology",
            change_type="unchanged",
            effective_class="routine",
            statement="Sem mudança.",
            publication_basis="automatic_routine",
            previous_values=("Drupal",),
            current_values=("Drupal",),
        )
        (snapshot / "events.json").write_text(
            json.dumps([initial.to_dict()], ensure_ascii=False), encoding="utf-8"
        )
        (snapshot / "manifest.json").write_text("{}", encoding="utf-8")
        self.ledger = AtomicLedger(Path(self.tempdir.name) / "ledger.jsonl")
        self.service = LongitudinalEventReviewService(self.ledger)
        self.store = PublicationRevisionStore(self.root)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_first_revision_preserves_initial_view(self) -> None:
        events = [{
            "event_id": "routine_1",
            "snapshot_id": self.snapshot_id,
            "corpus_code": "ina",
            "detector_group": "technology",
            "change_type": "unchanged",
            "triage_class": "routine",
            "review_required": False,
            "publication_status": "publishable",
            "previous_values": ["Drupal"],
            "current_values": ["Drupal"],
        }]
        original = (self.root / self.snapshot_id / "events.json").read_text(encoding="utf-8")
        manifest = regenerate_publication(
            snapshot_id=self.snapshot_id,
            events=events,
            review_service=self.service,
            store=self.store,
            reason="Revisão editorial de rotina.",
            requested_by="curator_1",
        )
        self.assertEqual(manifest.publication_revision, 1)
        self.assertIsNone(manifest.supersedes_revision_id)
        self.assertEqual(
            (self.root / self.snapshot_id / "events.json").read_text(encoding="utf-8"),
            original,
        )
        self.assertTrue(
            (self.root / self.snapshot_id / "revisions/revision_0001/manifest.json").exists()
        )

    def test_late_review_adds_event_and_second_revision_supersedes_first(self) -> None:
        events = [
            {
                "event_id": "routine_1",
                "snapshot_id": self.snapshot_id,
                "corpus_code": "ina",
                "detector_group": "technology",
                "change_type": "unchanged",
                "triage_class": "routine",
                "review_required": False,
                "publication_status": "publishable",
                "previous_values": ["Drupal"],
                "current_values": ["Drupal"],
            },
            {
                "event_id": "material_1",
                "snapshot_id": self.snapshot_id,
                "corpus_code": "ina",
                "detector_group": "api_service",
                "change_type": "appeared",
                "triage_class": "material_change",
                "review_required": True,
                "publication_status": "pending_review",
                "previous_values": [],
                "current_values": ["IIIF"],
            },
        ]
        first = regenerate_publication(
            snapshot_id=self.snapshot_id,
            events=events,
            review_service=self.service,
            store=self.store,
            reason="Primeira regeneração.",
            requested_by="curator_1",
        )
        self.assertEqual(first.event_count, 1)

        review = LongitudinalEventReview(
            event_id="material_1",
            reviewer_id="reviewer_1",
            reviewer_role="curator",
            decision="confirmed",
            justification="API confirmada na documentação.",
            evidence_ids=("evidence_1",),
        )
        self.service.register(review)
        second = regenerate_publication(
            snapshot_id=self.snapshot_id,
            events=events,
            review_service=self.service,
            store=self.store,
            reason="Incorporação de revisão humana tardia.",
            requested_by="curator_2",
        )
        self.assertEqual(second.publication_revision, 2)
        self.assertEqual(second.supersedes_revision_id, first.revision_id)
        self.assertEqual(second.added_event_ids, ("material_1",))
        self.assertIn(review.review_id, second.review_ids)

    def test_missing_initial_view_blocks_revision(self) -> None:
        store = PublicationRevisionStore(Path(self.tempdir.name) / "empty")
        with self.assertRaises(FileNotFoundError):
            store.write_revision(
                snapshot_id="missing",
                events=(),
                reason="Teste.",
                requested_by="curator",
            )


if __name__ == "__main__":
    unittest.main()
