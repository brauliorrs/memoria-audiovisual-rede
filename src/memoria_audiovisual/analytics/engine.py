"""Execução determinística e auditável dos indicadores registrados."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .base import IndicatorContext, IndicatorResult
from .registry import IndicatorRegistry


@dataclass(frozen=True, slots=True)
class AnalyticsRun:
    snapshot_id: str
    methodology_version: str
    indicator_count: int
    results: tuple[IndicatorResult, ...]
    status: str = "completed"
    errors: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["results"] = [item.to_dict() for item in self.results]
        payload["errors"] = list(self.errors)
        return payload


class AnalyticsEngine:
    """Executa indicadores sem modificar snapshots ou publicações de origem."""

    def __init__(self, registry: IndicatorRegistry, *, fail_fast: bool = True) -> None:
        self.registry = registry
        self.fail_fast = fail_fast

    def run(self, context: IndicatorContext) -> AnalyticsRun:
        results: list[IndicatorResult] = []
        errors: list[str] = []
        for indicator in self.registry:
            try:
                result = indicator.calculate(context)
                if result.indicator_id != indicator.indicator_id:
                    raise ValueError("resultado aponta para outro indicador")
                if result.indicator_version != indicator.version:
                    raise ValueError("resultado aponta para outra versão")
                if result.snapshot_id != context.snapshot_id:
                    raise ValueError("resultado aponta para outro snapshot")
                results.append(result)
            except Exception as exc:
                message = f"{indicator.indicator_id}@{indicator.version}: {exc}"
                if self.fail_fast:
                    raise RuntimeError(message) from exc
                errors.append(message)

        return AnalyticsRun(
            snapshot_id=context.snapshot_id,
            methodology_version=context.methodology_version,
            indicator_count=len(results),
            results=tuple(results),
            status="completed_with_errors" if errors else "completed",
            errors=tuple(errors),
        )
