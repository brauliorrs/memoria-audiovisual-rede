"""Fluxo append-only de revisão curatorial das observações técnicas."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Literal, Mapping

from .ids import stable_id
from .ledger import AtomicLedger
from .models import utc_now_iso

ReviewDecision = Literal[
    "confirmed", "probable", "inconclusive", "false_positive", "not_assessable", "needs_evidence"
]

SENSITIVE_GROUPS = {"ai_evidence", "restriction"}
SENSITIVE_TERMS = {
    "face recognition", "facial recognition", "reconhecimento facial",
    "biometric", "biometria", "personal data", "dados pessoais",
}


@dataclass(frozen=True, slots=True)
class CuratorialReview:
    observation_id: str
    reviewer_id: str
    reviewer_role: str
    decision: ReviewDecision
    justification: str
    evidence_ids: tuple[str, ...]
    conflict_of_interest_status: str = "none_declared"
    reviewed_at: str = field(default_factory=utc_now_iso)
    supersedes_review_id: str | None = None
    review_id: str = ""

    def __post_init__(self) -> None:
        if not self.observation_id.strip() or not self.reviewer_id.strip():
            raise ValueError("observation_id e reviewer_id são obrigatórios")
        if not self.justification.strip():
            raise ValueError("a justificativa da revisão é obrigatória")
        if not self.evidence_ids and self.decision in {"confirmed", "probable", "false_positive"}:
            raise ValueError("a decisão exige ao menos uma evidência")
        if not self.review_id:
            natural_key = "|".join(
                (self.observation_id, self.reviewer_id, self.reviewed_at, self.decision)
            )
            object.__setattr__(self, "review_id", stable_id("curatorial-review", natural_key))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_ids"] = list(self.evidence_ids)
        return data


@dataclass(frozen=True, slots=True)
class ReviewQueueItem:
    observation_id: str
    corpus_code: str
    institution_name: str
    detector_group: str
    detected_value: str
    automatic_confidence: str
    evidence_url: str
    current_status: str
    sensitive: bool
    required_confirmations: int


class CuratorialReviewService:
    """Registra decisões e produz o estado curatorial mais recente por observação."""

    def __init__(self, ledger: AtomicLedger) -> None:
        self.ledger = ledger

    def register(self, review: CuratorialReview) -> CuratorialReview:
        reviews = self.reviews_for(review.observation_id)
        if any(item.review_id == review.review_id for item in reviews):
            raise ValueError(f"revisão duplicada: {review.review_id}")
        if reviews:
            latest = reviews[-1]
            if review.supersedes_review_id != latest.review_id:
                raise ValueError("nova revisão deve substituir explicitamente a revisão mais recente")
        elif review.supersedes_review_id is not None:
            raise ValueError("primeira revisão não pode substituir revisão anterior")

        self.ledger.append(({"record_type": "curatorial_review", "payload": review.to_dict()},))
        return review

    def reviews_for(self, observation_id: str) -> tuple[CuratorialReview, ...]:
        found: list[CuratorialReview] = []
        for entry in self.ledger.read_all():
            for envelope in entry.records:
                if envelope.get("record_type") != "curatorial_review":
                    continue
                payload = dict(envelope.get("payload", {}))
                if payload.get("observation_id") != observation_id:
                    continue
                payload["evidence_ids"] = tuple(payload.get("evidence_ids", ()))
                found.append(CuratorialReview(**payload))
        return tuple(found)

    def latest(self, observation_id: str) -> CuratorialReview | None:
        reviews = self.reviews_for(observation_id)
        return reviews[-1] if reviews else None

    @staticmethod
    def is_sensitive(observation: Mapping[str, Any]) -> bool:
        group = str(observation.get("detector_group") or "").strip()
        text = " ".join(
            str(observation.get(name) or "").casefold()
            for name in ("detected_value", "evidence_value", "review_note")
        )
        return group in SENSITIVE_GROUPS or any(term in text for term in SENSITIVE_TERMS)

    def confirmation_count(self, observation_id: str) -> int:
        reviewers = {
            item.reviewer_id
            for item in self.reviews_for(observation_id)
            if item.decision == "confirmed"
            and item.conflict_of_interest_status not in {"declared_recusal_required", "under_assessment"}
        }
        return len(reviewers)

    def apply_latest(self, observation: Mapping[str, Any]) -> dict[str, Any]:
        observation_id = str(observation.get("observation_id") or "")
        review = self.latest(observation_id)
        if review is None:
            return dict(observation)
        result = dict(observation)
        result["review_status"] = (
            "pending_review" if review.decision == "needs_evidence" else review.decision
        )
        result["reviewed_at"] = review.reviewed_at
        result["reviewer"] = review.reviewer_id
        result["review_note"] = review.justification
        result["curatorial_review_id"] = review.review_id
        result["confirmation_count"] = self.confirmation_count(observation_id)
        return result

    def export_queue(
        self, observations: Iterable[Mapping[str, Any]], *, include_reviewed: bool = False
    ) -> tuple[ReviewQueueItem, ...]:
        queue: list[ReviewQueueItem] = []
        for observation in observations:
            observation_id = str(observation.get("observation_id") or "").strip()
            latest = self.latest(observation_id) if observation_id else None
            sensitive = self.is_sensitive(observation)
            required = 2 if sensitive else 1
            confirmations = self.confirmation_count(observation_id) if observation_id else 0
            complete = latest is not None and latest.decision != "needs_evidence" and confirmations >= required
            if complete and not include_reviewed:
                continue
            queue.append(
                ReviewQueueItem(
                    observation_id=observation_id,
                    corpus_code=str(observation.get("corpus_code") or ""),
                    institution_name=str(observation.get("institution_name") or ""),
                    detector_group=str(observation.get("detector_group") or ""),
                    detected_value=str(observation.get("detected_value") or ""),
                    automatic_confidence=str(observation.get("automatic_confidence") or ""),
                    evidence_url=str(observation.get("evidence_url") or ""),
                    current_status=(latest.decision if latest else str(observation.get("review_status") or "pending_review")),
                    sensitive=sensitive,
                    required_confirmations=required,
                )
            )
        return tuple(queue)

    def approved_for_materialization(
        self, observation: Mapping[str, Any]
    ) -> dict[str, Any] | None:
        reviewed = self.apply_latest(observation)
        if reviewed.get("review_status") != "confirmed":
            return None
        if reviewed.get("detection_status") != "detected":
            return None
        required = 2 if self.is_sensitive(reviewed) else 1
        if self.confirmation_count(str(reviewed.get("observation_id") or "")) < required:
            return None
        return reviewed
