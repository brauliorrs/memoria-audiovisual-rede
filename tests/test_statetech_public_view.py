from pathlib import Path

import pytest

from memoria_audiovisual.statetech.event_review import (
    LongitudinalEventReview,
    LongitudinalEventReviewService,
)
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.public_view import PublicViewStore, build_public_view


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


def test_rotina_e_incluida_sem_revisao(tmp_path: Path) -> None:
    service = LongitudinalEventReviewService(AtomicLedger(tmp_path / "ledger.jsonl"))
    event = _event(
        event_id="routine_1",
        change_type="unchanged",
        triage_class="routine",
        review_required=False,
        publication_status="publishable",
    )
    public = build_public_view([event], service)
    assert len(public) == 1
    assert public[0].publication_basis == "automatic_routine"
    assert public[0].review_ids == ()


def test_mudanca_material_sem_revisao_fica_fora(tmp_path: Path) -> None:
    service = LongitudinalEventReviewService(AtomicLedger(tmp_path / "ledger.jsonl"))
    assert build_public_view([_event()], service) == ()


def test_mudanca_confirmada_entra_com_rastreabilidade(tmp_path: Path) -> None:
    service = LongitudinalEventReviewService(AtomicLedger(tmp_path / "ledger.jsonl"))
    review = LongitudinalEventReview(
        event_id="event_1",
        reviewer_id="researcher_1",
        reviewer_role="curator",
        decision="confirmed",
        justification="A evidência confirma a alteração.",
        evidence_ids=("evidence_1",),
    )
    service.register(review)
    public = build_public_view([_event()], service)
    assert len(public) == 1
    assert public[0].publication_basis == "human_review_quorum"
    assert public[0].review_ids == (review.review_id,)
    assert public[0].evidence_ids == ("evidence_1",)


def test_desaparecimento_exige_dupla_confirmacao(tmp_path: Path) -> None:
    service = LongitudinalEventReviewService(AtomicLedger(tmp_path / "ledger.jsonl"))
    event = _event(
        event_id="event_disappearance",
        change_type="disappeared",
        triage_class="disappearance_alert",
        previous_values=["API"],
        current_values=[],
    )
    service.register(
        LongitudinalEventReview(
            event_id="event_disappearance",
            reviewer_id="r1",
            reviewer_role="curator",
            decision="confirmed",
            justification="Primeira confirmação.",
            evidence_ids=("ev1",),
        )
    )
    assert build_public_view([event], service) == ()
    service.register(
        LongitudinalEventReview(
            event_id="event_disappearance",
            reviewer_id="r2",
            reviewer_role="curator",
            decision="confirmed",
            justification="Segunda confirmação.",
            evidence_ids=("ev2",),
        )
    )
    public = build_public_view([event], service)
    assert len(public) == 1
    assert "não comprova eliminação definitiva" in public[0].statement


def test_store_versiona_e_bloqueia_sobrescrita(tmp_path: Path) -> None:
    service = LongitudinalEventReviewService(AtomicLedger(tmp_path / "ledger.jsonl"))
    event = _event(
        event_id="routine_1",
        change_type="baseline_created",
        triage_class="routine",
        review_required=False,
        publication_status="publishable",
    )
    public = build_public_view([event], service)
    store = PublicViewStore(tmp_path / "public")
    manifest = store.write("snapshot_2026_09", public)
    assert manifest.event_count == 1
    assert manifest.routine_count == 1
    assert (tmp_path / "public/snapshot_2026_09/events.json").exists()
    with pytest.raises(FileExistsError):
        store.write("snapshot_2026_09", public)
