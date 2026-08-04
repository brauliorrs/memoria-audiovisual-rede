"""Materialização e auditoria do Coverage Snapshot v1.0."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure.parameter_coverage import (
    EXPECTED_DETECTOR_GROUPS,
)

COVERAGE_SNAPSHOT_PATH = Path(
    "data/reference_corpus/snapshots/coverage_snapshot_v1.0.json"
)
SCIENTIFIC_SNAPSHOT_PATH = Path(
    "data/reference_corpus/snapshots/snapshot_v1.0.json"
)
REFERENCE_MANIFEST_PATH = Path("data/reference_corpus/manifest.json")


@dataclass(frozen=True, slots=True)
class CoverageSnapshotFinding:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class CoverageSnapshotReport:
    snapshot_id: str
    corpus_count: int
    parameter_count: int
    findings: tuple[CoverageSnapshotFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized_rows(
    rows: Iterable[Mapping[str, Any]], *, source_snapshot_id: str
) -> tuple[dict[str, Any], ...]:
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    canonical_codes = set(CORPORA)
    allowed_statuses = {
        "detected",
        "not_detected",
        "unknown",
        "error",
        "not_assessable",
        "missing_observation",
    }
    for position, source in enumerate(rows, start=1):
        if not isinstance(source, Mapping):
            raise ValueError(f"linha inválida na posição {position}")
        corpus_code = str(source.get("corpus_code") or "").strip()
        detector_group = str(source.get("detector_group") or "").strip()
        snapshot_id = str(source.get("snapshot_id") or "").strip()
        status = str(source.get("status") or "").strip()
        key = (corpus_code, detector_group)
        if corpus_code not in canonical_codes:
            raise ValueError(f"corpus não canônico: {corpus_code or '<vazio>'}")
        if detector_group not in EXPECTED_DETECTOR_GROUPS:
            raise ValueError(f"grupo detector inválido: {detector_group or '<vazio>'}")
        if snapshot_id != source_snapshot_id:
            raise ValueError(f"snapshot divergente na cobertura: {snapshot_id!r}")
        if status not in allowed_statuses:
            raise ValueError(f"estado de cobertura inválido: {status!r}")
        if key in seen:
            raise ValueError(f"cobertura duplicada: {corpus_code}/{detector_group}")
        seen.add(key)
        normalized.append(
            {
                "corpus_code": corpus_code,
                "detector_group": detector_group,
                "status": status,
                "observation_count": int(source.get("observation_count") or 0),
                "detected_values": sorted(
                    str(value) for value in source.get("detected_values", ())
                ),
            }
        )
    return tuple(
        sorted(normalized, key=lambda item: (item["corpus_code"], item["detector_group"]))
    )


def build_coverage_snapshot(
    *,
    coverage_rows: Iterable[Mapping[str, Any]],
    source_snapshot_id: str,
    started_at: str,
    finished_at: str,
    duration_seconds: float,
    pipeline_commit: str,
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    rows = _normalized_rows(coverage_rows, source_snapshot_id=source_snapshot_id)
    expected_pairs = {
        (corpus_code, group)
        for corpus_code in CORPORA
        for group in EXPECTED_DETECTOR_GROUPS
    }
    actual_pairs = {(row["corpus_code"], row["detector_group"]) for row in rows}
    missing = sorted(expected_pairs - actual_pairs)
    extra = sorted(actual_pairs - expected_pairs)
    if missing or extra:
        raise ValueError(
            f"matriz incompleta: ausentes={len(missing)}, excedentes={len(extra)}"
        )

    status_counts = Counter(row["status"] for row in rows)
    group_summary: dict[str, dict[str, Any]] = {}
    for group in EXPECTED_DETECTOR_GROUPS:
        group_rows = [row for row in rows if row["detector_group"] == group]
        group_counts = Counter(row["status"] for row in group_rows)
        evaluable = sum(
            group_counts.get(status, 0)
            for status in ("detected", "not_detected", "unknown")
        )
        detected = group_counts.get("detected", 0)
        group_summary[group] = {
            "corpus_count": len(group_rows),
            "detected": detected,
            "evaluable": evaluable,
            "coverage_percent": round(100 * detected / evaluable, 4)
            if evaluable
            else None,
            "status_counts": dict(sorted(group_counts.items())),
        }

    reference = manifest.get("reference_corpus") or {}
    dataset = manifest.get("dataset") or {}
    return {
        "coverage_snapshot": {
            "coverage_snapshot_id": "coverage_snapshot_v1_0",
            "version": "1.0.0",
            "status": "completed",
            "scientific_snapshot_id": "scientific_snapshot_v1_0",
            "source_snapshot_id": source_snapshot_id,
        },
        "reference_corpus": {
            "manifest_version": reference.get("version"),
            "source_content_hash": dataset.get("content_hash"),
            "entities": dataset.get("entities"),
        },
        "execution": {
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
            "pipeline_commit": pipeline_commit,
            "mode": "real_public_surface_audit",
        },
        "summary": {
            "corpus_count": len(CORPORA),
            "detector_group_count": len(EXPECTED_DETECTOR_GROUPS),
            "parameter_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
            "detector_groups": group_summary,
        },
        "coverage_rows": list(rows),
        "governance": {
            "derived_from_public_observations": True,
            "does_not_duplicate_corpus_definitions": True,
            "unknown_is_not_negative": True,
            "errors_are_not_counted_as_absence": True,
            "all_reference_corpus_units_included": True,
        },
    }


def audit_coverage_snapshot(repository_root: str | Path) -> CoverageSnapshotReport:
    root = Path(repository_root).resolve()
    path = root / COVERAGE_SNAPSHOT_PATH
    if not path.exists():
        return CoverageSnapshotReport(
            "",
            0,
            0,
            (CoverageSnapshotFinding("coverage_snapshot", "artefato ausente"),),
        )
    payload = _read_json(path)
    findings: list[CoverageSnapshotFinding] = []
    header = payload.get("coverage_snapshot") or {}
    corpus = payload.get("reference_corpus") or {}
    summary = payload.get("summary") or {}
    rows = payload.get("coverage_rows")
    governance = payload.get("governance") or {}
    manifest = _read_json(root / REFERENCE_MANIFEST_PATH)
    dataset = manifest.get("dataset") or {}

    if header.get("coverage_snapshot_id") != "coverage_snapshot_v1_0":
        findings.append(CoverageSnapshotFinding("coverage_snapshot_id", "identificador inválido"))
    if header.get("status") != "completed":
        findings.append(CoverageSnapshotFinding("status", "snapshot deve estar completed"))
    if corpus.get("source_content_hash") != dataset.get("content_hash"):
        findings.append(CoverageSnapshotFinding("source_content_hash", "hash divergente"))
    if corpus.get("entities") != len(CORPORA):
        findings.append(CoverageSnapshotFinding("entities", "quantidade divergente"))
    if not isinstance(rows, list):
        findings.append(CoverageSnapshotFinding("coverage_rows", "lista ausente"))
        rows = []
    expected_count = len(CORPORA) * len(EXPECTED_DETECTOR_GROUPS)
    if len(rows) != expected_count:
        findings.append(
            CoverageSnapshotFinding(
                "parameter_count", f"esperado={expected_count}, obtido={len(rows)}"
            )
        )
    if summary.get("parameter_count") != len(rows):
        findings.append(CoverageSnapshotFinding("summary.parameter_count", "contagem divergente"))
    for field in (
        "derived_from_public_observations",
        "does_not_duplicate_corpus_definitions",
        "unknown_is_not_negative",
        "errors_are_not_counted_as_absence",
        "all_reference_corpus_units_included",
    ):
        if governance.get(field) is not True:
            findings.append(CoverageSnapshotFinding(f"governance.{field}", "deve ser true"))
    try:
        normalized = _normalized_rows(
            (
                {
                    **row,
                    "snapshot_id": header.get("source_snapshot_id"),
                }
                for row in rows
            ),
            source_snapshot_id=str(header.get("source_snapshot_id") or ""),
        )
        if len(normalized) != expected_count:
            findings.append(CoverageSnapshotFinding("coverage_rows", "matriz incompleta"))
    except ValueError as exc:
        findings.append(CoverageSnapshotFinding("coverage_rows", str(exc)))

    return CoverageSnapshotReport(
        snapshot_id=str(header.get("coverage_snapshot_id") or ""),
        corpus_count=int(summary.get("corpus_count") or 0),
        parameter_count=int(summary.get("parameter_count") or 0),
        findings=tuple(findings),
    )


def assert_coverage_snapshot(report: CoverageSnapshotReport) -> None:
    if report.findings:
        raise ValueError(
            "; ".join(f"{item.field}: {item.message}" for item in report.findings)
        )
