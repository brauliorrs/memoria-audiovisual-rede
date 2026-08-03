"""Indicadores de cobertura derivados da matriz explícita por snapshot."""

from __future__ import annotations

from typing import Any, Mapping

from ..base import Indicator, IndicatorContext, IndicatorResult

_EVALUABLE_STATUSES = {"detected", "not_detected", "unknown"}


class DetectorCoverageIndicator(Indicator):
    detector_group: str

    def calculate(self, context: IndicatorContext) -> IndicatorResult:
        rows = [
            row for row in context.coverage_rows
            if str(row.get("detector_group") or "") == self.detector_group
        ]
        by_corpus: dict[str, Mapping[str, Any]] = {}
        for row in rows:
            corpus_code = str(row.get("corpus_code") or "").strip()
            if not corpus_code:
                raise ValueError("linha de cobertura sem corpus_code")
            if corpus_code in by_corpus:
                raise ValueError(
                    f"cobertura duplicada para {corpus_code}/{self.detector_group}"
                )
            by_corpus[corpus_code] = row

        evaluable = {
            corpus: row
            for corpus, row in by_corpus.items()
            if str(row.get("status") or "") in _EVALUABLE_STATUSES
        }
        detected = {
            corpus: row
            for corpus, row in evaluable.items()
            if str(row.get("status") or "") == "detected"
        }
        denominator = len(evaluable)
        numerator = len(detected)
        value = round((numerator / denominator) * 100, 4) if denominator else None
        excluded = tuple(sorted(set(context.corpus_codes) - set(evaluable)))
        status = "calculated" if denominator else "insufficient_data"
        notes = (
            "O denominador inclui apenas corpora com estado avaliável.",
            "Estados error, not_assessable e missing_observation são excluídos.",
        )
        return self.result(
            context,
            value=value,
            numerator=numerator,
            denominator=denominator,
            status=status,
            notes=notes,
            dimensions={
                "detector_group": self.detector_group,
                "detected_corpora": sorted(detected),
                "evaluable_corpora": sorted(evaluable),
                "excluded_corpora": list(excluded),
            },
        )


class ApiCoverageIndicator(DetectorCoverageIndicator):
    indicator_id = "api_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de APIs"
    category = "digital_infrastructure"
    unit = "percent"
    detector_group = "api_service"


class InteroperabilityCoverageIndicator(DetectorCoverageIndicator):
    indicator_id = "interoperability_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de interoperabilidade"
    category = "interoperability"
    unit = "percent"
    detector_group = "interoperability"
