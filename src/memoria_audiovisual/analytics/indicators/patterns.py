"""Indicadores de adoção de padrões específicos observados na cobertura."""

from __future__ import annotations

import re
from typing import Any, Mapping

from ..base import Indicator, IndicatorContext, IndicatorResult

_EVALUABLE_STATUSES = {"detected", "not_detected", "unknown"}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


class PatternCoverageIndicator(Indicator):
    detector_group: str
    aliases: tuple[str, ...]
    pattern_label: str

    def _matches(self, row: Mapping[str, Any]) -> bool:
        values = row.get("detected_values", ())
        if not isinstance(values, (list, tuple)):
            raise ValueError("detected_values deve ser uma lista")
        normalized_aliases = tuple(_normalize(alias) for alias in self.aliases)
        for raw in values:
            normalized = _normalize(str(raw))
            if any(alias == normalized or alias in normalized for alias in normalized_aliases):
                return True
        return False

    def calculate(self, context: IndicatorContext) -> IndicatorResult:
        rows = [
            row
            for row in context.coverage_rows
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
            if str(row.get("status") or "") == "detected" and self._matches(row)
        }
        denominator = len(evaluable)
        numerator = len(detected)
        value = round((numerator / denominator) * 100, 4) if denominator else None
        excluded = tuple(sorted(set(context.corpus_codes) - set(evaluable)))
        return self.result(
            context,
            value=value,
            numerator=numerator,
            denominator=denominator,
            status="calculated" if denominator else "insufficient_data",
            notes=(
                "O denominador inclui corpora com o grupo detector em estado avaliável.",
                "A presença é inferida somente a partir de detected_values normalizados.",
                "Estados error, not_assessable e missing_observation são excluídos.",
            ),
            dimensions={
                "pattern": self.pattern_label,
                "detector_group": self.detector_group,
                "aliases": list(self.aliases),
                "detected_corpora": sorted(detected),
                "evaluable_corpora": sorted(evaluable),
                "excluded_corpora": list(excluded),
            },
        )


class IiifCoverageIndicator(PatternCoverageIndicator):
    indicator_id = "iiif_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de IIIF"
    category = "interoperability"
    unit = "percent"
    detector_group = "interoperability"
    pattern_label = "IIIF"
    aliases = ("IIIF", "International Image Interoperability Framework")


class OaiPmhCoverageIndicator(PatternCoverageIndicator):
    indicator_id = "oai_pmh_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de OAI-PMH"
    category = "interoperability"
    unit = "percent"
    detector_group = "interoperability"
    pattern_label = "OAI-PMH"
    aliases = ("OAI-PMH", "Open Archives Initiative Protocol for Metadata Harvesting")


class DublinCoreCoverageIndicator(PatternCoverageIndicator):
    indicator_id = "dublin_core_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de Dublin Core"
    category = "metadata"
    unit = "percent"
    detector_group = "metadata_format"
    pattern_label = "Dublin Core"
    aliases = ("Dublin Core", "DCMI")


class SchemaOrgCoverageIndicator(PatternCoverageIndicator):
    indicator_id = "schema_org_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de Schema.org"
    category = "metadata"
    unit = "percent"
    detector_group = "metadata_format"
    pattern_label = "Schema.org"
    aliases = ("Schema.org", "schema org")


class JsonLdCoverageIndicator(PatternCoverageIndicator):
    indicator_id = "json_ld_coverage"
    version = "1.0.0"
    methodology_version = "1.0.0"
    title = "Cobertura de JSON-LD"
    category = "metadata"
    unit = "percent"
    detector_group = "metadata_format"
    pattern_label = "JSON-LD"
    aliases = ("JSON-LD", "JavaScript Object Notation for Linked Data")
