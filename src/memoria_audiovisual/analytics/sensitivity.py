"""Análise de sensibilidade para índices compostos sem alterar a metodologia oficial."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from .base import IndicatorContext
from .indicators.patterns import (
    DublinCoreCoverageIndicator,
    IiifCoverageIndicator,
    JsonLdCoverageIndicator,
    OaiPmhCoverageIndicator,
    PatternCoverageIndicator,
    SchemaOrgCoverageIndicator,
)

_EVALUABLE_STATUSES = {"detected", "not_detected", "unknown"}
_COMPONENTS: dict[str, PatternCoverageIndicator] = {
    "iiif": IiifCoverageIndicator(),
    "oai_pmh": OaiPmhCoverageIndicator(),
    "dublin_core": DublinCoreCoverageIndicator(),
    "schema_org": SchemaOrgCoverageIndicator(),
    "json_ld": JsonLdCoverageIndicator(),
}

DEFAULT_WEIGHT_SCENARIOS: dict[str, dict[str, float]] = {
    "official_equal_weights": {
        "iiif": 0.20,
        "oai_pmh": 0.20,
        "dublin_core": 0.20,
        "schema_org": 0.20,
        "json_ld": 0.20,
    },
    "protocol_priority": {
        "iiif": 0.30,
        "oai_pmh": 0.30,
        "dublin_core": 0.15,
        "schema_org": 0.10,
        "json_ld": 0.15,
    },
    "semantic_web_priority": {
        "iiif": 0.10,
        "oai_pmh": 0.10,
        "dublin_core": 0.20,
        "schema_org": 0.30,
        "json_ld": 0.30,
    },
    "audiovisual_delivery_priority": {
        "iiif": 0.40,
        "oai_pmh": 0.15,
        "dublin_core": 0.15,
        "schema_org": 0.15,
        "json_ld": 0.15,
    },
}


@dataclass(frozen=True, slots=True)
class SensitivityScenarioResult:
    scenario_id: str
    weights: Mapping[str, float]
    aggregate_score: float | None
    corpus_scores: Mapping[str, float]
    excluded_corpora: Mapping[str, str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["weights"] = dict(self.weights)
        payload["corpus_scores"] = dict(self.corpus_scores)
        payload["excluded_corpora"] = dict(self.excluded_corpora)
        return payload


@dataclass(frozen=True, slots=True)
class SensitivityReport:
    snapshot_id: str
    official_scenario: str
    minimum_evaluable_components: int
    scenarios: tuple[SensitivityScenarioResult, ...]
    aggregate_range: float | None
    maximum_corpus_variation: Mapping[str, float]
    rank_changes: Mapping[str, Mapping[str, int]]
    interpretation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "official_scenario": self.official_scenario,
            "minimum_evaluable_components": self.minimum_evaluable_components,
            "scenarios": [item.to_dict() for item in self.scenarios],
            "aggregate_range": self.aggregate_range,
            "maximum_corpus_variation": dict(self.maximum_corpus_variation),
            "rank_changes": {key: dict(value) for key, value in self.rank_changes.items()},
            "interpretation": self.interpretation,
        }


def _validate_scenarios(scenarios: Mapping[str, Mapping[str, float]]) -> None:
    expected = set(_COMPONENTS)
    if not scenarios:
        raise ValueError("ao menos um cenário de pesos é obrigatório")
    for scenario_id, weights in scenarios.items():
        if not str(scenario_id).strip():
            raise ValueError("scenario_id vazio")
        if set(weights) != expected:
            raise ValueError(f"cenário {scenario_id} não contém os cinco componentes")
        if any(float(value) < 0 for value in weights.values()):
            raise ValueError(f"cenário {scenario_id} contém peso negativo")
        total = sum(float(value) for value in weights.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"pesos do cenário {scenario_id} devem somar 1,0")


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


def _scenario_result(
    context: IndicatorContext,
    *,
    scenario_id: str,
    weights: Mapping[str, float],
    minimum_evaluable_components: int,
) -> SensitivityScenarioResult:
    rows = _rows_by_key(context)
    corpus_scores: dict[str, float] = {}
    excluded: dict[str, str] = {}

    for corpus in context.corpus_codes:
        weighted_sum = 0.0
        available_weight = 0.0
        evaluable_count = 0
        for component_id, component in _COMPONENTS.items():
            row = rows.get((corpus, component.detector_group))
            status = str(row.get("status") or "missing_observation") if row else "missing_observation"
            evaluable = row is not None and status in _EVALUABLE_STATUSES
            if not evaluable:
                continue
            evaluable_count += 1
            weight = float(weights[component_id])
            available_weight += weight
            if status == "detected" and component._matches(row):
                weighted_sum += weight

        if evaluable_count < minimum_evaluable_components or available_weight <= 0:
            excluded[corpus] = (
                f"apenas {evaluable_count} de {len(_COMPONENTS)} componentes avaliáveis"
            )
            continue
        corpus_scores[corpus] = round((weighted_sum / available_weight) * 100, 4)

    aggregate = (
        round(sum(corpus_scores.values()) / len(corpus_scores), 4)
        if corpus_scores
        else None
    )
    return SensitivityScenarioResult(
        scenario_id=scenario_id,
        weights=dict(weights),
        aggregate_score=aggregate,
        corpus_scores=corpus_scores,
        excluded_corpora=excluded,
    )


def _ranks(scores: Mapping[str, float]) -> dict[str, int]:
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    ranks: dict[str, int] = {}
    previous_score: float | None = None
    previous_rank = 0
    for position, (corpus, score) in enumerate(ordered, start=1):
        rank = previous_rank if previous_score == score else position
        ranks[corpus] = rank
        previous_score = score
        previous_rank = rank
    return ranks


def analyze_interoperability_sensitivity(
    context: IndicatorContext,
    *,
    scenarios: Mapping[str, Mapping[str, float]] = DEFAULT_WEIGHT_SCENARIOS,
    official_scenario: str = "official_equal_weights",
    minimum_evaluable_components: int = 3,
) -> SensitivityReport:
    """Compara esquemas de peso sem substituir o índice oficial persistido."""
    _validate_scenarios(scenarios)
    if official_scenario not in scenarios:
        raise ValueError("cenário oficial ausente")
    if minimum_evaluable_components < 1 or minimum_evaluable_components > len(_COMPONENTS):
        raise ValueError("minimum_evaluable_components inválido")

    results = tuple(
        _scenario_result(
            context,
            scenario_id=scenario_id,
            weights=weights,
            minimum_evaluable_components=minimum_evaluable_components,
        )
        for scenario_id, weights in scenarios.items()
    )
    aggregates = [
        item.aggregate_score for item in results if item.aggregate_score is not None
    ]
    aggregate_range = round(max(aggregates) - min(aggregates), 4) if aggregates else None

    all_corpora = sorted({corpus for item in results for corpus in item.corpus_scores})
    variations: dict[str, float] = {}
    for corpus in all_corpora:
        values = [item.corpus_scores[corpus] for item in results if corpus in item.corpus_scores]
        variations[corpus] = round(max(values) - min(values), 4) if values else 0.0

    official = next(item for item in results if item.scenario_id == official_scenario)
    official_ranks = _ranks(official.corpus_scores)
    rank_changes: dict[str, dict[str, int]] = {}
    for item in results:
        scenario_ranks = _ranks(item.corpus_scores)
        rank_changes[item.scenario_id] = {
            corpus: scenario_ranks[corpus] - official_ranks[corpus]
            for corpus in sorted(set(official_ranks).intersection(scenario_ranks))
        }

    if aggregate_range is None:
        interpretation = "Dados insuficientes para avaliar sensibilidade."
    elif aggregate_range <= 5:
        interpretation = "Resultado agregado robusto aos cenários de peso testados."
    elif aggregate_range <= 15:
        interpretation = "Resultado agregado moderadamente sensível aos pesos."
    else:
        interpretation = "Resultado agregado altamente sensível aos pesos; interpretação cautelosa recomendada."

    return SensitivityReport(
        snapshot_id=context.snapshot_id,
        official_scenario=official_scenario,
        minimum_evaluable_components=minimum_evaluable_components,
        scenarios=results,
        aggregate_range=aggregate_range,
        maximum_corpus_variation=variations,
        rank_changes=rank_changes,
        interpretation=interpretation,
    )
