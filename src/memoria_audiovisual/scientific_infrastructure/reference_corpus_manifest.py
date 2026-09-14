"""Validação executável do Scientific Reference Corpus Manifest."""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

MANIFEST_PATH = Path("data/reference_corpus/manifest.json")
INDICATOR_REGISTRY_PATH = Path("data/templates/analytics/indicator_registry.json")
METHODOLOGY_REGISTRY_PATH = Path("data/templates/analytics/methodology_registry.json")


@dataclass(frozen=True, slots=True)
class ReferenceCorpusFinding:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ReferenceCorpusReport:
    version: str
    dataset_path: str
    entity_count: int
    content_hash: str
    findings: tuple[ReferenceCorpusFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path}: raiz JSON deve ser objeto")
    return payload


def _git_blob_sha1(content: bytes) -> str:
    header = f"blob {len(content)}\0".encode("ascii")
    return hashlib.sha1(header + content).hexdigest()


def _literal_assignment_count(path: Path, selector: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == selector for target in targets):
            continue
        value = node.value
        if not isinstance(value, ast.Dict):
            raise ValueError(f"{selector} deve ser definido como dicionário literal")
        return len(value.keys)
    raise ValueError(f"seletor {selector!r} não localizado em {path}")


def _missing_report(field: str, message: str) -> ReferenceCorpusReport:
    return ReferenceCorpusReport(
        version="",
        dataset_path="",
        entity_count=0,
        content_hash="",
        findings=(ReferenceCorpusFinding(field, message),),
    )


def audit_reference_corpus_manifest(repository_root: str | Path) -> ReferenceCorpusReport:
    root = Path(repository_root).resolve()
    manifest_path = root / MANIFEST_PATH
    try:
        manifest = _read_json(manifest_path)
    except FileNotFoundError:
        return _missing_report("manifest", f"manifesto inexistente: {MANIFEST_PATH}")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return _missing_report("manifest", f"manifesto inválido: {exc}")

    reference = manifest.get("reference_corpus")
    dataset = manifest.get("dataset")
    context = manifest.get("scientific_context")
    governance = manifest.get("governance")
    findings: list[ReferenceCorpusFinding] = []

    for name, section in (
        ("reference_corpus", reference),
        ("dataset", dataset),
        ("scientific_context", context),
        ("governance", governance),
    ):
        if not isinstance(section, Mapping):
            findings.append(ReferenceCorpusFinding(name, "seção ausente ou inválida"))

    if findings:
        return ReferenceCorpusReport("", "", 0, "", tuple(findings))

    assert isinstance(reference, Mapping)
    assert isinstance(dataset, Mapping)
    assert isinstance(context, Mapping)
    assert isinstance(governance, Mapping)

    dataset_path = str(dataset.get("path") or "")
    selector = str(dataset.get("selector") or "")
    source = root / dataset_path
    expected_count = int(dataset.get("entities") or 0)
    expected_hash = str(dataset.get("content_hash") or "")

    if reference.get("manifest_id") != "scientific_reference_corpus_manifest":
        findings.append(ReferenceCorpusFinding("reference_corpus.manifest_id", "identificador inválido"))
    if reference.get("status") != "frozen":
        findings.append(ReferenceCorpusFinding("reference_corpus.status", "status deve ser frozen"))
    if dataset.get("hash_algorithm") != "git-blob-sha1":
        findings.append(ReferenceCorpusFinding("dataset.hash_algorithm", "algoritmo não suportado"))
    if not source.exists():
        findings.append(ReferenceCorpusFinding("dataset.path", f"dataset inexistente: {dataset_path}"))
        actual_count = 0
        actual_hash = ""
    else:
        content = source.read_bytes()
        actual_hash = _git_blob_sha1(content)
        try:
            actual_count = _literal_assignment_count(source, selector)
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
            actual_count = 0
            findings.append(ReferenceCorpusFinding("dataset.selector", str(exc)))

    if actual_count != expected_count:
        findings.append(
            ReferenceCorpusFinding(
                "dataset.entities",
                f"manifesto={expected_count}, fonte={actual_count}",
            )
        )
    if actual_hash != expected_hash:
        findings.append(
            ReferenceCorpusFinding(
                "dataset.content_hash",
                f"manifesto={expected_hash!r}, fonte={actual_hash!r}",
            )
        )

    try:
        indicator_payload = _read_json(root / INDICATOR_REGISTRY_PATH)
        indicator_version = str(
            (indicator_payload.get("registry") or {}).get("registry_version") or ""
        )
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        indicator_version = ""
        findings.append(
            ReferenceCorpusFinding(
                "scientific_context.indicator_registry_version",
                f"registro de indicadores indisponível: {exc}",
            )
        )

    try:
        methodology_payload = _read_json(root / METHODOLOGY_REGISTRY_PATH)
        methodology_version = str(methodology_payload.get("registry_version") or "")
    except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        methodology_version = ""
        findings.append(
            ReferenceCorpusFinding(
                "scientific_context.methodology_registry_version",
                f"registro metodológico indisponível: {exc}",
            )
        )

    if indicator_version and context.get("indicator_registry_version") != indicator_version:
        findings.append(
            ReferenceCorpusFinding(
                "scientific_context.indicator_registry_version",
                f"manifesto={context.get('indicator_registry_version')!r}, real={indicator_version!r}",
            )
        )
    if methodology_version and context.get("methodology_registry_version") != methodology_version:
        findings.append(
            ReferenceCorpusFinding(
                "scientific_context.methodology_registry_version",
                f"manifesto={context.get('methodology_registry_version')!r}, real={methodology_version!r}",
            )
        )

    required_governance = (
        "single_source_of_truth",
        "dataset_is_not_duplicated",
        "changes_require_new_manifest_version",
        "derived_snapshots_are_external_to_manifest",
    )
    for field in required_governance:
        if governance.get(field) is not True:
            findings.append(ReferenceCorpusFinding(f"governance.{field}", "deve ser true"))

    return ReferenceCorpusReport(
        version=str(reference.get("version") or ""),
        dataset_path=dataset_path,
        entity_count=actual_count,
        content_hash=actual_hash,
        findings=tuple(findings),
    )


def assert_reference_corpus_manifest(report: ReferenceCorpusReport) -> None:
    if report.findings:
        details = "; ".join(
            f"{finding.field}: {finding.message}" for finding in report.findings
        )
        raise ValueError(details)
