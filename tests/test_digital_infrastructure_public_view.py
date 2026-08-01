from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.event_review import (
    LongitudinalEventReview,
    LongitudinalEventReviewService,
)
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.public_view import PublicViewStore, build_public_view


def _event(**overrides):
    base = {
        "event_id": "event_1",
        "snapshot_id": "snapshot_2026_09",
        "corpus_code": "ina",
        "detector_group": "technology",
        "change_type": "appeared",
        "triage_class": "material_change",
        "review_required": True,
        "publication_status": "pending_review",
        "previous_values": [],
        "current_values": ["Drupal"],
    }
    base.update(overrides)
    return base


class PublicViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.service = LongitudinalEventReviewService(
            AtomicLedger(self.root / "ledger.jsonl")
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_rotina_e_incluida_sem_revisao(self) -> None:
        event = _event(
            event_id="routine_1",
            change_type="unchanged",
            triage_class="routine",
            review_required=False,
            publication_status="publishable",
        )
        public = build_public_view([event], self.service)
        self.assertEqual(len(public), 1)
        self.assertEqual(public[0].publication_basis, "automatic_routine")
        self.assertEqual(public[0].review_ids, ())

    def test_mudanca_material_sem_revisao_fica_fora(self) -> None:
        self.assertEqual(build_public_view([_event()], self.service), ())

    def test_mudanca_confirmada_entra_com_rastreabilidade(self) -> None:
        review = LongitudinalEventReview(
            event_id="event_1",
            reviewer_id="researcher_1",
            reviewer_role="curator",
            decision="confirmed",
            justification="A evidência confirma a alteração.",
            evidence_ids=("evidence_1",),
        )
        self.service.register(review)
        public = build_public_view([_event()], self.service)
        self.assertEqual(len(public), 1)
        self.assertEqual(public[0].publication_basis, "human_review_quorum")
        self.assertEqual(public[0].review_ids, (review.review_id,))
        self.assertEqual(public[0].evidence_ids, ("evidence_1",))

    def test_desaparecimento_exige_dupla_confirmacao(self) -> None:
        event = _event(
            event_id="event_disappearance",
            change_type="disappeared",
            triage_class="disappearance_alert",
            previous_values=["API"],
            current_values=[],
        )
        self.service.register(
            LongitudinalEventReview(
                event_id="event_disappearance",
                reviewer_id="r1",
                reviewer_role="curator",
                decision="confirmed",
                justification="Primeira confirmação.",
                evidence_ids=("ev1",),
            )
        )
        self.assertEqual(build_public_view([event], self.service), ())
        self.service.register(
            LongitudinalEventReview(
                event_id="event_disappearance",
                reviewer_id="r2",
                reviewer_role="curator",
                decision="confirmed",
                justification="Segunda confirmação.",
                evidence_ids=("ev2",),
            )
        )
        public = build_public_view([event], self.service)
        self.assertEqual(len(public), 1)
        self.assertIn("não comprova eliminação definitiva", public[0].statement)

    def test_store_versiona_e_bloqueia_sobrescrita(self) -> None:
        event = _event(
            event_id="routine_1",
            change_type="baseline_created",
            triage_class="routine",
            review_required=False,
            publication_status="publishable",
        )
        public = build_public_view([event], self.service)
        store = PublicViewStore(self.root / "public")
        manifest = store.write("snapshot_2026_09", public)
        self.assertEqual(manifest.event_count, 1)
        self.assertEqual(manifest.routine_count, 1)
        self.assertTrue((self.root / "public/snapshot_2026_09/events.json").exists())
        with self.assertRaises(FileExistsError):
            store.write("snapshot_2026_09", public)


if __name__ == "__main__":
    unittest.main()
