"""Materialização e auditoria do registro científico de resultados v1.0."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.engine import AnalyticsEngine
from memoria_audiovisual.analytics.pipeline import default_indicator_registry

COVERAGE_SNAPSHOT_PATH = Path(
    "data/reference_corpus/snapshots/coverage_snapshot_v1.0.json"
)
RESULTS_PATH = Path(
    "data/reference_corpus/snapshots/indicator_results_v1.0.json"
)
INDICATOR_REGISTRY_PATH = Path("data/templates/analytics/indicator_registry.json")
METHODOLOGY_REGISTRY_PATH = Path("data/templates/analytics/methodology_registry.json")
MANIFEST_PATH = Path("data/reference_corpus/manifest.json")


@dataclass(frozen=True, slots=True)
class IndicatorResultsFinding:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class IndicatorResultsReport:
    version: str
    status: str
    indicator_count: int
    findings: tuple[IndicatorResultsFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path}: raiz JSON deve ser objeto")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coverage_rows(payload: Mapping[str, Any]) -> tuple[dict[str, Any], ...]:
    identity = payload.get("coverage_snapshot") or {}
    snapshot_id = str(identity.get("coverage_snapshot_id") or "").strip()
    raw_rows = payload.get("coverage_rows")
    if not snapshot_id:
        raise ValueError("coverage snapshot sem identificador")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("coverage snapshot sem linhas de cobertura")

    rows: list[dict[str, Any]] = []
    for position, item in enumerate(raw_rows, start=1):
        if not isinstance(item, Mapping):
            raise ValueError(f"linha de cobertura inválida na posição {position}")
        row = dict(item)
        row["snapshot_id"] = snapshot_id
        rows.append(row)
    return tuple(rows)


def build_indicator_results_registry(
    repository_root: str | Path,
    *,
    created_at: str | None = None,
    pipeline_commit: str | None = None,
) -> dict[str, Any]:
    root = Path(repository_root).resolve()
    coverage_path = root / COVERAGE_SNAPSHOT_PATH
    coverage = _read_json(coverage_path)
    indicator_payload = _read_json(root / INDICATOR_REGISTRY_PATH)
    methodology_payload = _read_json(root / METHODOLOGY_REGISTRY_PATH)
    manifest_payload = _read_json(root / MANIFEST_PATH)

    coverage_identity = coverage.get("coverage_snapshot") or {}
    rows = _coverage_rows(coverage)
    methodology_version = str(methodology_payload.get("registry_version") or "")
    context = IndicatorContext(
        snapshot_id=str(coverage_identity.get("coverage_snapshot_id") or ""),
        coverage_rows=rows,
        methodology_version=methodology_version,
        metadata={
            "coverage_snapshot_path": str(COVERAGE_SNAPSHOT_PATH),
            "coverage_snapshot_sha256": _sha256(coverage_path),
        },
    )
    run = AnalyticsEngine(default_indicator_registry()).run(context)
    if run.status != "completed" or run.indicator_count != 9:
        raise ValueError(
            f"execução analítica incompleta: status={run.status}; "
            f"indicadores={run.indicator_count}"
        )

    timestamp = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    indicator_registry = indicator_payload.get("registry") or {}
    reference_corpus = manifest_payload.get("reference_corpus") or {}
    dataset = manifest_payload.get("dataset") or {}

    return {
        "artifact": {
            "artifact_id": "scientific_indicator_results_v1_0",
            "type": "indicator_results",
            "version": "1.0.0",
            "status": "completed",
            "created_at": timestamp,
            "pipeline_stage": "2C.3",
        },
        "provenance": {
            "scientific_snapshot_id": "scientific_snapshot_v1_0",
            "coverage_snapshot_id": coverage_identity.get("coverage_snapshot_id"),
            "coverage_snapshot_path": str(COVERAGE_SNAPSHOT_PATH),
            "coverage_snapshot_sha256": _sha256(coverage_path),
            "reference_corpus_version": reference_corpus.get("version"),
            "reference_corpus_hash": dataset.get("content_hash"),
            "indicator_registry_version": indicator_registry.get("registry_version"),
            "methodology_registry_version": methodology_version,
            "pipeline_commit": pipeline_commit,
        },
        "content": {
            "indicator_count": run.indicator_count,
            "execution_status": run.status,
            "results": [item.to_dict() for item in run.results],
        },
        "governance": {
            "derived_from_coverage_snapshot": True,
            "does_not_modify_source_artifacts": True,
            "results_are_engine_generated": True,
            "methodologies_are_referenced_not_duplicated": True,
        },
    }


def write_indicator_results_registry(
    repository_root: str | Path,
    *,
    output_path: str | Path | None = None,
    created_at: str | None = None,
    pipeline_commit: str | None = None,
) -> Path:
    root = Path(repository_root).resolve()
    destination = root / (Path(output_path) if output_path else RESULTS_PATH)
    if destination.exists():
        raise FileExistsError(f"registro de resultados já existe: {destination}")
    payload = build_indicator_results_registry(
        root,
        created_at=created_at,
        pipeline_commit=pipeline_commit,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def audit_indicator_results_registry(
    repository_root: str | Path,
) -> IndicatorResultsReport:
    root = Path(repository_root).resolve()
    path = root / RESULTS_PATH
    if not path.exists():
        return IndicatorResultsReport(
            "",
            "missing",
            0,
            (IndicatorResultsFinding("artifact", "registro de resultados ausente"),),
        )

    stored = _read_json(path)
    artifact = stored.get("artifact") or {}
    provenance = stored.get("provenance") or {}
    content = stored.get("content") or {}
    governance = stored.get("governance") or {}
    findings: list[IndicatorResultsFinding] = []

    expected = build_indicator_results_registry(
        root,
        created_at=str(artifact.get("created_at") or ""),
        pipeline_commit=provenance.get("pipeline_commit"),
    )
    if stored != expected:
        findings.append(
            IndicatorResultsFinding(
                "artifact",
                "registro materializado diverge do motor ou dos artefatos de origem",
            )
        )

    results = content.get("results")
    if not isinstance(results, list):
        results = []
        findings.append(IndicatorResultsFinding("content.results", "lista ausente"))

    ids = [str(item.get("indicator_id") or "") for item in results if isinstance(item, Mapping)]
    if len(results) != 9 or content.get("indicator_count") != 9:
        findings.append(IndicatorResultsFinding("content.indicator_count", "devem existir exatamente 9 indicadores"))
    if len(ids) != len(set(ids)):
        findings.append(IndicatorResultsFinding("content.results", "indicadores duplicados"))

    registry = _read_json(root / INDICATOR_REGISTRY_PATH)
    registered = {
        str(item.get("indicator_id") or "")
        for item in registry.get("indicators", [])
        if isinstance(item, Mapping)
    }
    if set(ids) != registered:
        findings.append(IndicatorResultsFinding("content.results", "IDs divergem do registro canônico"))

    for field in (
        "derived_from_coverage_snapshot",
        "does_not_modify_source_artifacts",
        "results_are_engine_generated",
        "methodologies_are_referenced_not_duplicated",
    ):
        if governance.get(field) is not True:
            findings.append(IndicatorResultsFinding(f"governance.{field}", "deve ser true"))

    return IndicatorResultsReport(
        version=str(artifact.get("version") or ""),
        status=str(artifact.get("status") or ""),
        indicator_count=len(results),
        findings=tuple(findings),
    )


def assert_indicator_results_registry(report: IndicatorResultsReport) -> None:
    if report.findings:
        details = "; ".join(f"{item.field}: {item.message}" for item in report.findings)
        raise ValueError(details)
