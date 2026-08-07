"""Adaptador analítico para o registro canônico de indicadores."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .registry import IndicatorRegistry

_REQUIRED_TEXT_FIELDS = (
    "indicator_id",
    "indicator_version",
    "title",
    "scientific_question",
    "selection_rationale",
    "dimension",
    "interpretation",
    "relationship_to_other_indicators",
    "methodology_reference",
)


@dataclass(frozen=True, slots=True)
class IndicatorCatalog:
    """Visão compatível do registro canônico usada pelo motor analítico.

    O nome da classe é preservado para compatibilidade da API interna. A fonte
    oficial, porém, é ``indicator_registry.json``.
    """

    catalog_version: str
    entries: tuple[Mapping[str, Any], ...]

    @classmethod
    def load(cls, path: str | Path) -> "IndicatorCatalog":
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(f"registro de indicadores inexistente: {source}")
        payload = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(payload, Mapping):
            raise ValueError("registro deve conter um objeto JSON")

        registry_metadata = payload.get("registry")
        if registry_metadata is not None and not isinstance(registry_metadata, Mapping):
            raise ValueError("registry deve conter um objeto JSON")
        metadata = registry_metadata if isinstance(registry_metadata, Mapping) else payload
        version = str(
            metadata.get("registry_version")
            or payload.get("registry_version")
            or payload.get("catalog_version")
            or ""
        ).strip()
        if not version:
            raise ValueError("registry_version é obrigatório")

        raw_entries = payload.get("indicators")
        if not isinstance(raw_entries, list) or not raw_entries:
            raise ValueError("registro deve conter uma lista não vazia de indicadores")
        entries: list[Mapping[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for position, raw in enumerate(raw_entries, start=1):
            if not isinstance(raw, Mapping):
                raise ValueError(f"entrada inválida no registro: posição {position}")
            missing = [
                field
                for field in _REQUIRED_TEXT_FIELDS
                if not str(raw.get(field) or "").strip()
            ]
            if missing:
                raise ValueError(
                    f"entrada {position} sem campos obrigatórios: {', '.join(missing)}"
                )
            limitations = raw.get("does_not_measure")
            if not isinstance(limitations, list) or not limitations:
                raise ValueError(
                    f"entrada {position} deve declarar ao menos uma limitação em does_not_measure"
                )
            key = (str(raw["indicator_id"]), str(raw["indicator_version"]))
            if key in seen:
                raise ValueError(f"entrada duplicada no registro: {key[0]}@{key[1]}")
            seen.add(key)
            entries.append(dict(raw))
        return cls(catalog_version=version, entries=tuple(entries))

    def validate_registry(self, registry: IndicatorRegistry) -> None:
        catalog_keys = {
            (str(entry["indicator_id"]), str(entry["indicator_version"]))
            for entry in self.entries
        }
        registry_keys = {
            (indicator.indicator_id, indicator.version) for indicator in registry
        }
        missing = sorted(registry_keys - catalog_keys)
        orphaned = sorted(catalog_keys - registry_keys)
        if missing:
            formatted = ", ".join(f"{item[0]}@{item[1]}" for item in missing)
            raise ValueError(f"indicadores registrados sem explicação no registro: {formatted}")
        if orphaned:
            formatted = ", ".join(f"{item[0]}@{item[1]}" for item in orphaned)
            raise ValueError(f"entradas do registro sem indicador registrado: {formatted}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_version": self.catalog_version,
            "indicator_count": len(self.entries),
            "indicators": [dict(entry) for entry in self.entries],
        }
