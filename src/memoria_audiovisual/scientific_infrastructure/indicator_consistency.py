"""Auditoria de consistência do registro científico de indicadores.

A identidade científica é comparada com o catálogo legado durante a migração.
Regras operacionais de elegibilidade, como ``corpus_rule``, podem ser refinadas
no registro canônico sem alterar o conceito medido. A disponibilidade
metodológica é reportada separadamente, pois fórmulas e regras de cálculo
pertencem ao Methodology Registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


IDENTITY_FIELDS = (
    "indicator_version",
    "title",
    "scientific_question",
    "selection_rationale",
    "dimension",
    "interpretation",
    "does_not_measure",
    "relationship_to_other_indicators",
    "methodology_reference",
)

# Campos operacionais podem ganhar maior precisão durante a consolidação sem
# representar mudança da identidade científica do indicador.
OPERATIONAL_FIELDS = ("corpus_rule",)


@dataclass(frozen=True, slots=True)
class IndicatorConsistencyReport:
    canonical_ids: tuple[str, ...]
    legacy_ids: tuple[str, ...]
    methodology_ids: tuple[str, ...]
    missing_from_canonical: tuple[str, ...]
    absent_from_legacy: tuple[str, ...]
    identity_divergences: tuple[str, ...]
    operational_refinements: tuple[str, ...]
    missing_methodologies: tuple[str, ...]
    orphan_methodologies: tuple[str, ...]

    @property
    def identity_is_consolidated(self) -> bool:
        return not (
            self.missing_from_canonical
            or self.absent_from_legacy
            or self.identity_divergences
        )

    @property
    def methodology_is_complete(self) -> bool:
        return not (self.missing_methodologies or self.orphan_methodologies)

    @property
    def blocking_errors(self) -> tuple[str, ...]:
        errors: list[str] = []
        errors.extend(f"ausente no registro canônico: {item}" for item in self.missing_from_canonical)
        errors.extend(f"ausente no catálogo legado: {item}" for item in self.absent_from_legacy)
        errors.extend(self.identity_divergences)
        return tuple(errors)


def _by_id(rows: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    return {
        str(row.get("indicator_id")): row
        for row in rows
        if isinstance(row, Mapping) and row.get("indicator_id")
    }


def compare_indicator_sources(
    canonical_indicators: Iterable[Mapping[str, Any]],
    legacy_indicators: Iterable[Mapping[str, Any]],
    methodologies: Iterable[Mapping[str, Any]],
) -> IndicatorConsistencyReport:
    canonical = _by_id(canonical_indicators)
    legacy = _by_id(legacy_indicators)
    methodology = _by_id(methodologies)

    canonical_ids = set(canonical)
    legacy_ids = set(legacy)
    methodology_ids = set(methodology)

    divergences: list[str] = []
    operational_refinements: list[str] = []
    for indicator_id in sorted(canonical_ids & legacy_ids):
        current = canonical[indicator_id]
        previous = legacy[indicator_id]
        for field in IDENTITY_FIELDS:
            if current.get(field) != previous.get(field):
                divergences.append(f"{indicator_id}.{field}: divergência de identidade")

        for field in OPERATIONAL_FIELDS:
            if current.get(field) != previous.get(field):
                operational_refinements.append(
                    f"{indicator_id}.{field}: refinamento operacional"
                )

        methodology_id = current.get("methodology_id")
        if methodology_id != indicator_id:
            divergences.append(
                f"{indicator_id}.methodology_id: deve corresponder ao indicator_id"
            )

    return IndicatorConsistencyReport(
        canonical_ids=tuple(sorted(canonical_ids)),
        legacy_ids=tuple(sorted(legacy_ids)),
        methodology_ids=tuple(sorted(methodology_ids)),
        missing_from_canonical=tuple(sorted(legacy_ids - canonical_ids)),
        absent_from_legacy=tuple(sorted(canonical_ids - legacy_ids)),
        identity_divergences=tuple(divergences),
        operational_refinements=tuple(operational_refinements),
        missing_methodologies=tuple(sorted(canonical_ids - methodology_ids)),
        orphan_methodologies=tuple(sorted(methodology_ids - canonical_ids)),
    )


def assert_consolidated_identity(report: IndicatorConsistencyReport) -> None:
    """Bloqueia divergências científicas, sem confundir refinamentos operacionais."""
    if report.blocking_errors:
        raise ValueError("; ".join(report.blocking_errors))
