"""Contratos imutáveis e versionados do motor analítico."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class IndicatorContext:
    """Dados de entrada de uma execução analítica sobre um único snapshot."""

    snapshot_id: str
    coverage_rows: tuple[Mapping[str, Any], ...]
    methodology_version: str = "1.0.0"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.snapshot_id.strip():
            raise ValueError("snapshot_id é obrigatório")
        snapshots = {
            str(row.get("snapshot_id") or "").strip()
            for row in self.coverage_rows
            if str(row.get("snapshot_id") or "").strip()
        }
        if snapshots and snapshots != {self.snapshot_id}:
            raise ValueError("coverage_rows contém dados de outro snapshot")

    @property
    def corpus_codes(self) -> tuple[str, ...]:
        return tuple(sorted({
            str(row.get("corpus_code") or "").strip()
            for row in self.coverage_rows
            if str(row.get("corpus_code") or "").strip()
        }))


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    indicator_id: str
    indicator_version: str
    methodology_version: str
    snapshot_id: str
    title: str
    category: str
    value: float | int | str | None
    unit: str
    numerator: int | float | None = None
    denominator: int | float | None = None
    corpus_count: int = 0
    status: str = "calculated"
    notes: tuple[str, ...] = ()
    dimensions: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["notes"] = list(self.notes)
        payload["dimensions"] = dict(self.dimensions)
        return payload


class Indicator(ABC):
    """Contrato explícito para indicadores reproduzíveis e registráveis."""

    indicator_id: str
    version: str
    title: str
    category: str
    unit: str
    methodology_version: str = "1.0.0"

    def validate_definition(self) -> None:
        required = {
            "indicator_id": self.indicator_id,
            "version": self.version,
            "title": self.title,
            "category": self.category,
            "unit": self.unit,
            "methodology_version": self.methodology_version,
        }
        missing = [name for name, value in required.items() if not str(value).strip()]
        if missing:
            raise ValueError(f"definição incompleta do indicador: {', '.join(missing)}")

    @abstractmethod
    def calculate(self, context: IndicatorContext) -> IndicatorResult:
        """Calcula o indicador sem alterar os dados de origem."""

    def result(
        self,
        context: IndicatorContext,
        *,
        value: float | int | str | None,
        numerator: int | float | None = None,
        denominator: int | float | None = None,
        status: str = "calculated",
        notes: Sequence[str] = (),
        dimensions: Mapping[str, Any] | None = None,
    ) -> IndicatorResult:
        self.validate_definition()
        return IndicatorResult(
            indicator_id=self.indicator_id,
            indicator_version=self.version,
            methodology_version=self.methodology_version,
            snapshot_id=context.snapshot_id,
            title=self.title,
            category=self.category,
            value=value,
            unit=self.unit,
            numerator=numerator,
            denominator=denominator,
            corpus_count=len(context.corpus_codes),
            status=status,
            notes=tuple(notes),
            dimensions=dict(dimensions or {}),
        )
