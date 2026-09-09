"""Contrato executável do registro científico de indicadores."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


REGISTRY_RELATIVE_PATH = Path("data/templates/analytics/indicator_registry.json")
REQUIRED_REGISTRY_FIELDS = {
    "registry_id",
    "name",
    "platform",
    "registry_version",
    "schema_version",
    "language",
    "status",
    "indicator_count",
    "compatibility",
    "governance",
}
REQUIRED_INDICATOR_FIELDS = {
    "indicator_id",
    "indicator_version",
    "status",
    "title",
    "scientific_question",
    "scientific_rationale",
    "selection_rationale",
    "dimension",
    "unit",
    "expected_range",
    "result_type",
    "interpretation",
    "does_not_measure",
    "relationship_to_other_indicators",
    "corpus_rule",
    "evidence_requirements",
    "dependencies",
    "methodology_id",
    "methodology_reference",
}


class IndicatorRegistryError(ValueError):
    """Indica violação do contrato canônico do registro."""


@dataclass(frozen=True, slots=True)
class IndicatorRegistry:
    metadata: Mapping[str, Any]
    indicators: tuple[Mapping[str, Any], ...]

    @property
    def version(self) -> str:
        return str(self.metadata["registry_version"])

    @property
    def indicator_ids(self) -> tuple[str, ...]:
        return tuple(str(item["indicator_id"]) for item in self.indicators)

    def get(self, indicator_id: str) -> Mapping[str, Any]:
        for indicator in self.indicators:
            if indicator["indicator_id"] == indicator_id:
                return indicator
        raise KeyError(indicator_id)


def _missing_fields(payload: Mapping[str, Any], required: Iterable[str]) -> list[str]:
    return sorted(field for field in required if field not in payload)


def _validate_range(indicator: Mapping[str, Any]) -> None:
    expected_range = indicator.get("expected_range")
    if not isinstance(expected_range, Mapping):
        raise IndicatorRegistryError(
            f"{indicator.get('indicator_id', '<unknown>')}: expected_range deve ser objeto"
        )
    minimum = expected_range.get("minimum")
    maximum = expected_range.get("maximum")
    if not isinstance(minimum, (int, float)) or not isinstance(maximum, (int, float)):
        raise IndicatorRegistryError(
            f"{indicator['indicator_id']}: intervalo esperado deve ser numérico"
        )
    if minimum >= maximum:
        raise IndicatorRegistryError(
            f"{indicator['indicator_id']}: intervalo esperado inválido"
        )


def validate_indicator_registry(payload: Mapping[str, Any]) -> IndicatorRegistry:
    metadata = payload.get("registry")
    indicators = payload.get("indicators")
    if not isinstance(metadata, Mapping):
        raise IndicatorRegistryError("Metadados do registro ausentes ou inválidos")
    if not isinstance(indicators, list):
        raise IndicatorRegistryError("Lista de indicadores ausente ou inválida")

    missing_registry = _missing_fields(metadata, REQUIRED_REGISTRY_FIELDS)
    if missing_registry:
        raise IndicatorRegistryError(
            f"Campos obrigatórios ausentes no registro: {missing_registry}"
        )

    normalized: list[Mapping[str, Any]] = []
    ids: list[str] = []
    for index, indicator in enumerate(indicators):
        if not isinstance(indicator, Mapping):
            raise IndicatorRegistryError(f"Indicador na posição {index} não é objeto")
        missing = _missing_fields(indicator, REQUIRED_INDICATOR_FIELDS)
        if missing:
            raise IndicatorRegistryError(
                f"Campos ausentes em {indicator.get('indicator_id', index)}: {missing}"
            )
        indicator_id = str(indicator["indicator_id"]).strip()
        if not indicator_id:
            raise IndicatorRegistryError(f"Indicador na posição {index} sem ID")
        ids.append(indicator_id)
        if indicator["methodology_id"] != indicator_id:
            raise IndicatorRegistryError(
                f"{indicator_id}: methodology_id deve coincidir com indicator_id"
            )
        if not isinstance(indicator["does_not_measure"], list):
            raise IndicatorRegistryError(
                f"{indicator_id}: does_not_measure deve ser lista"
            )
        if not isinstance(indicator["evidence_requirements"], list):
            raise IndicatorRegistryError(
                f"{indicator_id}: evidence_requirements deve ser lista"
            )
        if not isinstance(indicator["dependencies"], list):
            raise IndicatorRegistryError(f"{indicator_id}: dependencies deve ser lista")
        _validate_range(indicator)
        normalized.append(indicator)

    duplicates = sorted({item for item in ids if ids.count(item) > 1})
    if duplicates:
        raise IndicatorRegistryError(f"IDs duplicados: {duplicates}")

    declared_count = metadata["indicator_count"]
    if declared_count != len(normalized):
        raise IndicatorRegistryError(
            f"indicator_count={declared_count}, mas foram encontrados {len(normalized)}"
        )

    unknown_dependencies = sorted(
        {
            str(dependency)
            for indicator in normalized
            for dependency in indicator["dependencies"]
            if dependency not in ids
        }
    )
    if unknown_dependencies:
        raise IndicatorRegistryError(
            f"Dependências não registradas: {unknown_dependencies}"
        )

    return IndicatorRegistry(metadata=metadata, indicators=tuple(normalized))


def load_indicator_registry(base_dir: str | Path) -> IndicatorRegistry:
    path = Path(base_dir) / REGISTRY_RELATIVE_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise IndicatorRegistryError(f"Registro não localizado: {path}") from exc
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndicatorRegistryError(f"Registro inválido: {path}: {exc}") from exc
    if not isinstance(payload, Mapping):
        raise IndicatorRegistryError("A raiz do registro deve ser um objeto JSON")
    return validate_indicator_registry(payload)
