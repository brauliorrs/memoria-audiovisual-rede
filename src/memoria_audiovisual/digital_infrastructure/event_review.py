"""Revisão humana append-only de eventos longitudinais triados."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal, Mapping

from .ids import stable_id
from .ledger import AtomicLedger
from .models import utc_now_iso

EventReviewDecision = Literal[
    "confirmed", "rejected", "reclassified", "needs_evidence", "deferred"
]

HIGH_RISK_CLASSES = {"disappearance_alert", "sensitive"}
ALLOWED_RECLASSIFICATIONS = {
    "routine", "material_change", "disappearance_alert", "sensitive", "data_quality", "unclassified"
}


@dataclass(frozen=True, slots=True)
class LongitudinalEventReview:
    event_id: str
    reviewer_id: str
    reviewer_role: str
    decision: EventReviewDecision
    justification: str
    evidence_ids: tuple[str, ...] = ()
    reclassified_as: str | None = None
    conflict_of_interest_status: str = "none_declared"
    reviewed_at: str = field(default_factory=utc_now_iso)
    supersedes_review_id: str | None = None
    review_id: str = ""

    def __post_init__(self) -> None:
        if not self.event_id.strip() or not self.reviewer_id.strip() or not self.reviewer_role.strip():
            raise ValueError("event_id, reviewer_id e reviewer_role são obrigatórios")
        if not self.justification.strip():
            raise ValueError("a justificativa é obrigatória")
        if self.decision in {"confirmed", "rejected", "reclassified"} and not self.evidence_ids:
            raise ValueError("a decisão exige ao menos uma evidência")
        if self.decision == "reclassified":
            if self.reclassified_as not in ALLOWED_RECLASSIFICATIONS:
                raise ValueError("reclassified_as inválido")
        elif self.reclassified_as is not None:
            raise ValueError("reclassified_as só pode ser usado com decisão reclassified")
        if not self.review_id:
            basis = "|".join((self.event_id, self.reviewer_id, self.reviewed_at, self.decision))
            object.__setattr__(self, "review_id", stable_id("event-review", basis))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True, slots=True)
class EventReviewState:
    event_id: str
    current_status: str
    effective_class: str
    confirmation_count: int
    required_confirmations: int
    publication_status: str
    latest_review_id: str | None


class LongitudinalEventReviewService:
    def __init__(self, ledger: AtomicLedger) -> None:
        self.ledger = ledger

    def register(self, review: LongitudinalEventReview) -> LongitudinalEventReview:
        reviews = self.reviews_for(review.event_id)
        if any(item.review_id == review.review_id for item in reviews):
            raise ValueError(f"revisão duplicada: {review.review_id}")
        reviewer_latest = next((item for item in reversed(reviews) if item.reviewer_id == review.reviewer_id), None)
        if reviewer_latest is not None and review.supersedes_review_id != reviewer_latest.review_id:
            raise ValueError("nova decisão do mesmo revisor deve substituir explicitamente sua decisão anterior")
        if reviewer_latest is None and review.supersedes_review_id is not None:
            raise ValueError("primeira decisão do revisor não pode substituir revisão anterior")
        self.ledger.append(({"record_type": "longitudinal_event_review", "payload": review.to_dict()},))
        return review

    def reviews_for(self, event_id: str) -> tuple[LongitudinalEventReview, ...]:
        found: list[LongitudinalEventReview] = []
        for entry in self.ledger.read_all():
            for envelope in entry.records:
                if envelope.get("record_type") != "longitudinal_event_review":
                    continue
                payload = dict(envelope.get("payload", {}))
                if payload.get("event_id") != event_id:
                    continue
                payload["evidence_ids"] = tuple(payload.get("evidence_ids", ()))
                found.append(LongitudinalEventReview(**payload))
        return tuple(found)

    @staticmethod
    def required_confirmations(event: Mapping[str, Any]) -> int:
        return 2 if str(event.get("triage_class") or "") in HIGH_RISK_CLASSES else 1

    def current_state(self, event: Mapping[str, Any]) -> EventReviewState:
        event_id = str(event.get("event_id") or "").strip()
        if not event_id:
            raise ValueError("evento sem event_id")
        reviews = self.reviews_for(event_id)
        active_by_reviewer: dict[str, LongitudinalEventReview] = {}
        for review in reviews:
            active_by_reviewer[review.reviewer_id] = review
        eligible = [
            item for item in active_by_reviewer.values()
            if item.conflict_of_interest_status not in {"declared_recusal_required", "under_assessment"}
        ]
        confirmations = [item for item in eligible if item.decision == "confirmed"]
        required = self.required_confirmations(event)
        latest = reviews[-1] if reviews else None
        effective_class = str(event.get("triage_class") or "unclassified")
        reclassifications = [item for item in eligible if item.decision == "reclassified"]
        if reclassifications:
            effective_class = str(reclassifications[-1].reclassified_as)

        if any(item.decision == "rejected" for item in eligible):
            status, publication = "rejected", "blocked"
        elif len({item.reviewer_id for item in confirmations}) >= required:
            status = "confirmed"
            publication = "publishable_after_review"
        elif latest and latest.decision == "needs_evidence":
            status, publication = "needs_evidence", "blocked"
        elif latest and latest.decision == "deferred":
            status, publication = "deferred", "blocked"
        elif reclassifications:
            status, publication = "reclassified_pending_confirmation", "pending_review"
        else:
            status, publication = "pending_review", "pending_review"

        return EventReviewState(
            event_id=event_id,
            current_status=status,
            effective_class=effective_class,
            confirmation_count=len({item.reviewer_id for item in confirmations}),
            required_confirmations=required,
            publication_status=publication,
            latest_review_id=latest.review_id if latest else None,
        )

    def export_queue(self, events: Iterable[Mapping[str, Any]], *, include_resolved: bool = False) -> tuple[dict[str, Any], ...]:
        queue: list[dict[str, Any]] = []
        for event in events:
            if not bool(event.get("review_required")):
                continue
            state = self.current_state(event)
            if not include_resolved and state.current_status in {"confirmed", "rejected"}:
                continue
            row = dict(event)
            row.update(asdict(state))
            queue.append(row)
        return tuple(queue)

    def approved_for_public_view(self, event: Mapping[str, Any]) -> dict[str, Any] | None:
        state = self.current_state(event)
        if state.current_status != "confirmed":
            return None
        result = dict(event)
        result["triage_class"] = state.effective_class
        result["publication_status"] = state.publication_status
        result["event_review_status"] = state.current_status
        result["event_review_confirmation_count"] = state.confirmation_count
        return result
