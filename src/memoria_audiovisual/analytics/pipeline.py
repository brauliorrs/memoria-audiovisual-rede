"""Orquestração da análise de um snapshot de cobertura consolidado."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .base import IndicatorContext
from .engine import AnalyticsEngine, AnalyticsRun
from .indicators import (
    ApiCoverageIndicator,
    DublinCoreCoverageIndicator,
    IiifCoverageIndicator,
    InteroperabilityCoverageIndicator,
    JsonLdCoverageIndicator,
    OaiPmhCoverageIndicator,
    SchemaOrgCoverageIndicator,
)
from .registry import IndicatorRegistry
from .storage import AnalyticsManifest, AnalyticsStore


@dataclass(frozen=True, slots=True)
class SnapshotAnalyticsResult:
    run: AnalyticsRun
    manifest: AnalyticsManifest | None


def default_indicator_registry() -> IndicatorRegistry:
    """Retorna o conjunto nativo e explicitamente versionado de indicadores."""
    return IndicatorRegistry((
        ApiCoverageIndicator(),
        DublinCoreCoverageIndicator(),
        IiifCoverageIndicator(),
        InteroperabilityCoverageIndicator(),
        JsonLdCoverageIndicator(),
        OaiPmhCoverageIndicator(),
        SchemaOrgCoverageIndicator(),
    ))


def load_coverage_rows(path: str | Path, *, snapshot_id: str) -> tuple[dict[str, Any], ...]:
    """Carrega e valida a matriz de cobertura de um único snapshot."""
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"matriz de cobertura inexistente: {source}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("parameter_coverage.json deve conter uma lista")

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for position, item in enumerate(payload, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"linha de cobertura inválida na posição {position}")
        row = dict(item)
        row_snapshot = str(row.get("snapshot_id") or "").strip()
        corpus_code = str(row.get("corpus_code") or "").strip()
        detector_group = str(row.get("detector_group") or "").strip()
        if row_snapshot != snapshot_id:
            raise ValueError(
                f"linha de cobertura aponta para outro snapshot: {row_snapshot or '<vazio>'}"
            )
        if not corpus_code or not detector_group:
            raise ValueError("linha de cobertura sem corpus_code ou detector_group")
        key = (corpus_code, detector_group)
        if key in seen:
            raise ValueError(
                f"cobertura duplicada para corpus e parâmetro: {corpus_code}|{detector_group}"
            )
        seen.add(key)
        rows.append(row)
    if not rows:
        raise ValueError("matriz de cobertura vazia")
    return tuple(rows)


def analyze_snapshot(
    *,
    snapshot_id: str,
    coverage_path: str | Path,
    methodology_version: str = "1.0.0",
    registry: IndicatorRegistry | None = None,
    output_root: str | Path | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> SnapshotAnalyticsResult:
    """Executa indicadores registrados e, opcionalmente, persiste o resultado."""
    rows = load_coverage_rows(coverage_path, snapshot_id=snapshot_id)
    context = IndicatorContext(
        snapshot_id=snapshot_id,
        coverage_rows=rows,
        methodology_version=methodology_version,
        metadata=dict(metadata or {}),
    )
    active_registry = registry or default_indicator_registry()
    run = AnalyticsEngine(active_registry).run(context)
    manifest = AnalyticsStore(output_root).write(run) if output_root is not None else None
    return SnapshotAnalyticsResult(run=run, manifest=manifest)
