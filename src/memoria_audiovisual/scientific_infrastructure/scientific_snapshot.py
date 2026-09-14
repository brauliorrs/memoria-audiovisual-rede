"""Contrato do Scientific Snapshot v1.0."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SNAPSHOT_PATH = Path("data/reference_corpus/snapshots/snapshot_v1.0.json")
MANIFEST_PATH = Path("data/reference_corpus/manifest.json")
INDICATOR_REGISTRY_PATH = Path("data/templates/analytics/indicator_registry.json")
METHODOLOGY_REGISTRY_PATH = Path("data/templates/analytics/methodology_registry.json")


@dataclass(frozen=True, slots=True)
class ScientificSnapshotFinding:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ScientificSnapshotReport:
    version: str
    status: str
    entity_count: int
    findings: tuple[ScientificSnapshotFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path}: raiz JSON deve ser objeto")
    return payload


def audit_scientific_snapshot(repository_root: str | Path) -> ScientificSnapshotReport:
    root = Path(repository_root).resolve()
    snapshot_path = root / SNAPSHOT_PATH
    if not snapshot_path.exists():
        return ScientificSnapshotReport(
            "",
            "missing",
            0,
            (ScientificSnapshotFinding("snapshot", "snapshot científico ausente"),),
        )

    snapshot_payload = _read_json(snapshot_path)
    manifest_payload = _read_json(root / MANIFEST_PATH)
    indicator_payload = _read_json(root / INDICATOR_REGISTRY_PATH)
    methodology_payload = _read_json(root / METHODOLOGY_REGISTRY_PATH)

    snapshot = snapshot_payload.get("snapshot")
    corpus = snapshot_payload.get("reference_corpus")
    context = snapshot_payload.get("scientific_context")
    execution = snapshot_payload.get("execution")
    materialization = snapshot_payload.get("materialization")
    governance = snapshot_payload.get("governance")
    findings: list[ScientificSnapshotFinding] = []

    for name, section in (
        ("snapshot", snapshot),
        ("reference_corpus", corpus),
        ("scientific_context", context),
        ("execution", execution),
        ("materialization", materialization),
        ("governance", governance),
    ):
        if not isinstance(section, Mapping):
            findings.append(ScientificSnapshotFinding(name, "seção ausente ou inválida"))

    if findings:
        return ScientificSnapshotReport("", "invalid", 0, tuple(findings))

    assert isinstance(snapshot, Mapping)
    assert isinstance(corpus, Mapping)
    assert isinstance(context, Mapping)
    assert isinstance(execution, Mapping)
    assert isinstance(materialization, Mapping)
    assert isinstance(governance, Mapping)

    manifest_reference = manifest_payload.get("reference_corpus") or {}
    manifest_dataset = manifest_payload.get("dataset") or {}
    indicator_registry = indicator_payload.get("registry") or {}

    if snapshot.get("snapshot_id") != "scientific_snapshot_v1_0":
        findings.append(ScientificSnapshotFinding("snapshot.snapshot_id", "identificador inválido"))
    if snapshot.get("status") not in {"initialized", "completed"}:
        findings.append(ScientificSnapshotFinding("snapshot.status", "estado não suportado"))
    if corpus.get("manifest_path") != str(MANIFEST_PATH):
        findings.append(ScientificSnapshotFinding("reference_corpus.manifest_path", "caminho divergente"))
    if corpus.get("manifest_version") != manifest_reference.get("version"):
        findings.append(ScientificSnapshotFinding("reference_corpus.manifest_version", "versão divergente"))
    if corpus.get("source_content_hash") != manifest_dataset.get("content_hash"):
        findings.append(ScientificSnapshotFinding("reference_corpus.source_content_hash", "hash divergente"))
    if corpus.get("entities") != manifest_dataset.get("entities"):
        findings.append(ScientificSnapshotFinding("reference_corpus.entities", "quantidade divergente"))

    actual_indicator_version = indicator_registry.get("registry_version")
    actual_methodology_version = methodology_payload.get("registry_version")
    if context.get("indicator_registry_version") != actual_indicator_version:
        findings.append(ScientificSnapshotFinding("scientific_context.indicator_registry_version", "versão divergente"))
    if context.get("methodology_registry_version") != actual_methodology_version:
        findings.append(ScientificSnapshotFinding("scientific_context.methodology_registry_version", "versão divergente"))

    initialized = snapshot.get("status") == "initialized"
    if initialized:
        if execution.get("status") != "not_executed":
            findings.append(ScientificSnapshotFinding("execution.status", "snapshot inicializado deve estar not_executed"))
        for field in ("started_at", "finished_at", "duration_seconds", "pipeline_commit"):
            if execution.get(field) is not None:
                findings.append(ScientificSnapshotFinding(f"execution.{field}", "deve permanecer nulo antes da execução"))
        for field in (
            "coverage_snapshot_available",
            "indicator_results_available",
            "provenance_available",
        ):
            if materialization.get(field) is not False:
                findings.append(ScientificSnapshotFinding(f"materialization.{field}", "deve ser false antes da materialização"))
        if not str(materialization.get("absence_reason") or "").strip():
            findings.append(ScientificSnapshotFinding("materialization.absence_reason", "ausência deve ser explicada"))

    for field in (
        "does_not_duplicate_corpus",
        "does_not_fabricate_results",
        "execution_metadata_required_before_completion",
        "derived_results_must_reference_snapshot",
    ):
        if governance.get(field) is not True:
            findings.append(ScientificSnapshotFinding(f"governance.{field}", "deve ser true"))

    return ScientificSnapshotReport(
        version=str(snapshot.get("version") or ""),
        status=str(snapshot.get("status") or ""),
        entity_count=int(corpus.get("entities") or 0),
        findings=tuple(findings),
    )


def assert_scientific_snapshot(report: ScientificSnapshotReport) -> None:
    if report.findings:
        details = "; ".join(f"{item.field}: {item.message}" for item in report.findings)
        raise ValueError(details)
