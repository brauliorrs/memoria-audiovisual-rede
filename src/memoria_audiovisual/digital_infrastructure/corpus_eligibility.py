"""Política explícita de descoberta, classificação e elegibilidade do corpus."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

ELIGIBLE = "eligible"
EXCLUDED = "excluded"

EXCLUSION_REASONS = {
    "commercial_image_bank",
    "commercial_video_bank",
    "commercial_media_platform",
    "news_portal",
    "search_engine",
    "social_media",
    "aggregator",
    "duplicate",
    "inactive",
    "outside_scope",
    "other",
}

PAID_BANK_CATEGORIES = {
    "commercial_image_bank",
    "commercial_video_bank",
}


@dataclass(frozen=True, slots=True)
class CorpusEligibilityDecision:
    entity_id: str
    entity_category: str
    corpus_status: str
    exclusion_reason: str | None
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_corpus_eligibility(entity: Mapping[str, Any]) -> CorpusEligibilityDecision:
    """Classifica uma entidade descoberta sem apagá-la do registro de descoberta.

    Bancos comerciais pagos de imagens ou vídeos são catalogados, mas não
    integram o corpus científico nem denominadores analíticos.
    """
    entity_id = str(entity.get("entity_id") or entity.get("corpus_code") or "").strip()
    category = str(entity.get("entity_category") or entity.get("category") or "other").strip()
    is_paid = bool(entity.get("is_paid") or entity.get("commercial_access"))
    if not entity_id:
        raise ValueError("entity_id ou corpus_code é obrigatório")

    if category in PAID_BANK_CATEGORIES or (is_paid and category in {"image_bank", "video_bank"}):
        reason = "commercial_image_bank" if "image" in category else "commercial_video_bank"
        return CorpusEligibilityDecision(
            entity_id=entity_id,
            entity_category=category,
            corpus_status=EXCLUDED,
            exclusion_reason=reason,
            rationale=(
                "Entidade identificada e catalogada no registro de descoberta, "
                "mas excluída do corpus por operar como banco comercial pago."
            ),
        )

    declared_status = str(entity.get("corpus_status") or ELIGIBLE).strip()
    reason = str(entity.get("exclusion_reason") or "").strip() or None
    if declared_status == EXCLUDED:
        if reason not in EXCLUSION_REASONS:
            raise ValueError("exclusion_reason inválido para entidade excluída")
        return CorpusEligibilityDecision(
            entity_id=entity_id,
            entity_category=category,
            corpus_status=EXCLUDED,
            exclusion_reason=reason,
            rationale=str(entity.get("eligibility_rationale") or "Entidade fora do corpus científico."),
        )
    if declared_status != ELIGIBLE:
        raise ValueError("corpus_status deve ser eligible ou excluded")
    return CorpusEligibilityDecision(
        entity_id=entity_id,
        entity_category=category,
        corpus_status=ELIGIBLE,
        exclusion_reason=None,
        rationale=str(entity.get("eligibility_rationale") or "Entidade elegível para o corpus científico."),
    )


def eligible_corpus_codes(entities: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...]) -> tuple[str, ...]:
    """Retorna somente unidades aptas a integrar análises e denominadores."""
    return tuple(sorted(
        decision.entity_id
        for decision in (classify_corpus_eligibility(entity) for entity in entities)
        if decision.corpus_status == ELIGIBLE
    ))
