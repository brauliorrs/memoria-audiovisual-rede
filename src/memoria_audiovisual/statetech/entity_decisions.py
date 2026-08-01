"""Decisões curatoriais de merge, split e redirecionamento."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from .ids import stable_id
from .models import utc_now_iso

DecisionType = Literal["merge", "split", "redirect", "keep_separate"]
DecisionStatus = Literal["proposed", "approved", "rejected", "superseded"]


@dataclass(frozen=True, slots=True)
class EntityDecision:
    decision_type: DecisionType
    source_entity_ids: tuple[str, ...]
    target_entity_ids: tuple[str, ...]
    rationale: str
    decided_by: str
    evidence_ids: tuple[str, ...] = ()
    status: DecisionStatus = "proposed"
    decided_at: str = field(default_factory=utc_now_iso)
    supersedes_decision_id: str | None = None
    decision_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        if not self.source_entity_ids:
            raise ValueError("a decisão exige ao menos uma entidade de origem")
        if self.decision_type in {"merge", "redirect"} and len(self.target_entity_ids) != 1:
            raise ValueError(f"{self.decision_type} exige exatamente uma entidade de destino")
        if self.decision_type == "split" and len(self.target_entity_ids) < 2:
            raise ValueError("split exige ao menos duas entidades de destino")
        if set(self.source_entity_ids) & set(self.target_entity_ids):
            raise ValueError("origem e destino não podem conter o mesmo identificador")

        data = asdict(self)
        data["source_entity_ids"] = list(self.source_entity_ids)
        data["target_entity_ids"] = list(self.target_entity_ids)
        data["evidence_ids"] = list(self.evidence_ids)
        natural_key = "|".join(
            [self.decision_type, *sorted(self.source_entity_ids), "->", *sorted(self.target_entity_ids), self.decided_at]
        )
        data["decision_id"] = self.decision_id or stable_id("entity-decision", natural_key)
        return data


def build_redirect_map(decisions: tuple[EntityDecision, ...]) -> dict[str, str]:
    """Materializa apenas decisões aprovadas de merge ou redirect."""
    redirects: dict[str, str] = {}
    for decision in decisions:
        if decision.status != "approved" or decision.decision_type not in {"merge", "redirect"}:
            continue
        target = decision.target_entity_ids[0]
        for source in decision.source_entity_ids:
            existing = redirects.get(source)
            if existing is not None and existing != target:
                raise ValueError(f"redirecionamento conflitante para {source}")
            redirects[source] = target
    return redirects
