"""Índices compostos versionados e transparentes."""

from __future__ import annotations

from typing import Any, Mapping

from ..base import Indicator, IndicatorContext, IndicatorResult
from .patterns import (
    DublinCoreCoverageIndicator,
    IiifCoverageIndicator,
    JsonLdCoverageIndicator,
    OaiPmhCoverageIndicator,
    PatternCoverageIndicator,
    SchemaOrgCoverageIndicator,
)

_EVALUABLE_STATUSES = {"detected", "not_detected", "unknown"}


class InteroperabilityIndexIndicator(Indicator):
    """Média dos escores por corpus para cinco componentes interoperáveis."""

    indicator_id = "interoperability_index"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Índice de interoperabilidade"
    category = "composite_index"
    unit = "score_0_100"
    minimum_evaluable_components = 3
    components: tuple[tuple[PatternCoverageIndicator, float], ...] = (
        (IiifCoverageIndicator(), 0.20),
        (OaiPmhCoverageIndicator(), 0.20),
        (DublinCoreCoverageIndicator(), 0.20),
        (SchemaOrgCoverageIndicator(), 0.20),
        (JsonLdCoverageIndicator(), 0.20),
    )

    @staticmethod
    def _rows_by_key(context: IndicatorContext) -> dict[tuple[str, str], Mapping[str, Any]]:
        rows: dict[tuple[str, str], Mapping[str, Any]] = {}
        for row in context.coverage_rows:
            corpus = str(row.get("corpus_code") or "").strip()
            group = str(row.get("detector_group") or "").strip()
            if not corpus or not group:
                continue
            key = (corpus, group)
            if key in rows:
                raise ValueError(f"cobertura duplicada para {corpus}/{group}")
            rows[key] = row
        return rows

    def calculate(self, context: IndicatorContext) -> IndicatorResult:
        rows = self._rows_by_key(context)
        corpus_scores: dict[str, float] = {}
        corpus_components: dict[str, dict[str, Any]] = {}
        excluded: dict[str, str] = {}

        for corpus in context.corpus_codes:
            weighted_sum = 0.0
            available_weight = 0.0
            component_state: dict[str, Any] = {}

            for component, weight in self.components:
                row = rows.get((corpus, component.detector_group))
                status = str(row.get("status") or "missing_observation") if row else "missing_observation"
                evaluable = row is not None and status in _EVALUABLE_STATUSES
                present = bool(
                    evaluable
                    and status == "detected"
                    and component._matches(row)
                )
                component_state[component.pattern_label] = {
                    "weight": weight,
                    "status": status,
                    "evaluable": evaluable,
                    "present": present,
                }
                if evaluable:
                    available_weight += weight
                    weighted_sum += weight if present else 0.0

            evaluable_count = sum(
                bool(item["evaluable"]) for item in component_state.values()
            )
            if evaluable_count < self.minimum_evaluable_components or available_weight <= 0:
                excluded[corpus] = (
                    f"apenas {evaluable_count} de {len(self.components)} componentes avaliáveis"
                )
                corpus_components[corpus] = component_state
                continue

            score = round((weighted_sum / available_weight) * 100, 4)
            corpus_scores[corpus] = score
            corpus_components[corpus] = component_state

        value = (
            round(sum(corpus_scores.values()) / len(corpus_scores), 4)
            if corpus_scores
            else None
        )
        return self.result(
            context,
            value=value,
            numerator=sum(corpus_scores.values()) if corpus_scores else None,
            denominator=len(corpus_scores),
            status="calculated" if corpus_scores else "insufficient_data",
            notes=(
                "Os cinco componentes possuem peso igual de 0,20.",
                "Pesos ausentes são renormalizados somente quando ao menos três componentes são avaliáveis.",
                "O valor agregado é a média aritmética dos escores dos corpora elegíveis.",
                "O índice mede sinais observados, não conformidade técnica integral.",
            ),
            dimensions={
                "weights": {
                    component.pattern_label: weight
                    for component, weight in self.components
                },
                "minimum_evaluable_components": self.minimum_evaluable_components,
                "eligible_corpora": sorted(corpus_scores),
                "excluded_corpora": excluded,
                "corpus_scores": corpus_scores,
                "component_states": corpus_components,
            },
        )
