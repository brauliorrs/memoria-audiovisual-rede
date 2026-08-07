"""Modelo de apresentação do registro científico de indicadores.

Converte o contrato canônico em estruturas prontas para a interface, sem
redefinir conceitos, fórmulas ou regras metodológicas no Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


DIMENSION_LABELS = {
    "access": "Acesso",
    "digital_infrastructure": "Infraestrutura digital",
    "interoperability": "Interoperabilidade",
    "metadata": "Metadados",
    "composite_index": "Índice composto",
}

STATUS_LABELS = {
    "implemented": "Implementado",
    "active": "Ativo",
    "experimental": "Experimental",
    "deprecated": "Descontinuado",
}

UNIT_LABELS = {
    "percent": "Percentual",
    "percentage": "Percentual",
    "score": "Pontuação",
    "index": "Índice",
    "boolean": "Sim/não",
}


@dataclass(frozen=True, slots=True)
class IndicatorPresentation:
    indicator_id: str
    title: str
    version: str
    status: str
    scientific_question: str
    scientific_rationale: str
    selection_rationale: str
    dimension: str
    unit: str
    expected_range: str
    result_type: str
    interpretation: str
    does_not_measure: tuple[str, ...]
    relationship_to_other_indicators: str
    corpus_rule: str
    evidence_requirements: tuple[str, ...]
    dependencies: tuple[str, ...]
    methodology_id: str
    methodology_reference: str
    methodology_available: bool
    formula: str


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _expected_range(value: object) -> str:
    if not isinstance(value, Mapping):
        return "—"
    minimum = value.get("minimum")
    maximum = value.get("maximum")
    if minimum is None and maximum is None:
        return "—"
    if minimum is None:
        return f"até {maximum}"
    if maximum is None:
        return f"a partir de {minimum}"
    return f"{minimum} a {maximum}"


def _label(mapping: Mapping[str, str], value: object) -> str:
    raw = str(value or "").strip()
    return mapping.get(raw, raw or "—")


def build_indicator_presentations(
    indicators: Iterable[Mapping[str, Any]],
    methodologies_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[IndicatorPresentation, ...]:
    presentations: list[IndicatorPresentation] = []
    for indicator in indicators:
        indicator_id = str(indicator.get("indicator_id", "")).strip()
        methodology_id = str(indicator.get("methodology_id", indicator_id)).strip()
        methodology = methodologies_by_id.get(methodology_id, {})
        presentations.append(
            IndicatorPresentation(
                indicator_id=indicator_id,
                title=str(indicator.get("title", indicator_id) or indicator_id),
                version=str(indicator.get("indicator_version", "—")),
                status=_label(STATUS_LABELS, indicator.get("status")),
                scientific_question=str(indicator.get("scientific_question", "—")),
                scientific_rationale=str(indicator.get("scientific_rationale", "—")),
                selection_rationale=str(indicator.get("selection_rationale", "—")),
                dimension=_label(DIMENSION_LABELS, indicator.get("dimension")),
                unit=_label(UNIT_LABELS, indicator.get("unit")),
                expected_range=_expected_range(indicator.get("expected_range")),
                result_type=str(indicator.get("result_type", "—")),
                interpretation=str(indicator.get("interpretation", "—")),
                does_not_measure=_strings(indicator.get("does_not_measure")),
                relationship_to_other_indicators=str(
                    indicator.get("relationship_to_other_indicators", "—")
                ),
                corpus_rule=str(indicator.get("corpus_rule", "—")),
                evidence_requirements=_strings(indicator.get("evidence_requirements")),
                dependencies=_strings(indicator.get("dependencies")),
                methodology_id=methodology_id or "—",
                methodology_reference=str(indicator.get("methodology_reference", "—")),
                methodology_available=bool(methodology),
                formula=str(methodology.get("formula", "")),
            )
        )
    return tuple(presentations)


def registry_summary(registry_payload: Mapping[str, Any]) -> dict[str, object]:
    metadata = registry_payload.get("registry")
    indicators = registry_payload.get("indicators")
    metadata = metadata if isinstance(metadata, Mapping) else {}
    indicators = indicators if isinstance(indicators, list) else []
    dimensions = {
        str(item.get("dimension"))
        for item in indicators
        if isinstance(item, Mapping) and item.get("dimension")
    }
    return {
        "name": metadata.get("name", "Registro científico de indicadores"),
        "version": metadata.get("registry_version", "—"),
        "status": _label(STATUS_LABELS, metadata.get("status")),
        "language": metadata.get("language", "—"),
        "indicator_count": len(indicators),
        "dimension_count": len(dimensions),
        "methodology_registry_version": metadata.get(
            "methodology_registry_version", "—"
        ),
    }
