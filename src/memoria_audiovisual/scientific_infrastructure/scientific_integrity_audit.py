"""Contrato permanente de integridade da infraestrutura científica."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from memoria_audiovisual.analytics.pipeline import default_indicator_registry

from .indicator_registry import IndicatorRegistry, load_indicator_registry
from .methodology_consistency_audit import audit_methodologies
from .reference_corpus_manifest import audit_reference_corpus_manifest
from .single_source_audit import find_duplicate_definitions

METHODOLOGY_PATH = Path("data/templates/analytics/methodology_registry.json")
LEGACY_CATALOG_PATH = Path("data/templates/analytics/indicator_catalog.json")
INTERFACE_PATH = Path("src/memoria_audiovisual/ui/scientific_infrastructure.py")
ALLOWED_PENDING_METHODOLOGIES: frozenset[str] = frozenset()
INTERFACE_CONTRACT_TOKENS = (
    "build_indicator_presentations",
    "registry_summary",
    "scientific_rationale",
    "evidence_requirements",
    "methodology_reference",
    "expected_range",
)


@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    contract: str
    message: str


@dataclass(frozen=True, slots=True)
class ScientificIntegrityReport:
    registry_version: str
    indicator_count: int
    implementation_count: int
    methodology_count: int
    pending_methodologies: tuple[str, ...]
    findings: tuple[IntegrityFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path}: raiz JSON deve ser objeto")
    return payload


def _methodology_payload(root: Path) -> Mapping[str, Any]:
    return _read_json(root / METHODOLOGY_PATH)


def _methodologies(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = payload.get("methodologies")
    if not isinstance(rows, list):
        raise ValueError("methodology_registry.json: methodologies deve ser lista")
    result: dict[str, Mapping[str, Any]] = {}
    for position, row in enumerate(rows, start=1):
        if not isinstance(row, Mapping):
            raise ValueError(f"metodologia inválida na posição {position}")
        indicator_id = str(row.get("indicator_id") or "").strip()
        if not indicator_id:
            raise ValueError(f"metodologia sem indicator_id na posição {position}")
        if indicator_id in result:
            raise ValueError(f"metodologia duplicada: {indicator_id}")
        result[indicator_id] = row
    return result


def _implementation_findings(registry: IndicatorRegistry) -> tuple[IntegrityFinding, ...]:
    implementations = {
        item.indicator_id: item for item in default_indicator_registry()
    }
    canonical = {str(item["indicator_id"]): item for item in registry.indicators}
    findings: list[IntegrityFinding] = []

    for indicator_id in sorted(canonical.keys() - implementations.keys()):
        findings.append(IntegrityFinding("registry_implementation", f"sem implementação: {indicator_id}"))
    for indicator_id in sorted(implementations.keys() - canonical.keys()):
        findings.append(IntegrityFinding("registry_implementation", f"implementação sem registro: {indicator_id}"))

    for indicator_id in sorted(canonical.keys() & implementations.keys()):
        definition = canonical[indicator_id]
        implementation = implementations[indicator_id]
        comparisons = {
            "indicator_version": (str(definition["indicator_version"]), implementation.version),
            "unit": (str(definition["unit"]), implementation.unit),
            "dimension/category": (str(definition["dimension"]), implementation.category),
        }
        for field, (expected, actual) in comparisons.items():
            if expected != actual:
                findings.append(
                    IntegrityFinding(
                        "registry_implementation",
                        f"{indicator_id}.{field}: registro={expected!r}, motor={actual!r}",
                    )
                )
    return tuple(findings)


def _methodology_findings(
    registry: IndicatorRegistry,
    methodology_payload: Mapping[str, Any],
    methodologies: Mapping[str, Mapping[str, Any]],
) -> tuple[tuple[str, ...], tuple[IntegrityFinding, ...]]:
    canonical_ids = set(registry.indicator_ids)
    methodology_ids = set(methodologies)
    pending = tuple(sorted(canonical_ids - methodology_ids))
    findings: list[IntegrityFinding] = []

    declared_version = str(registry.metadata.get("methodology_registry_version") or "")
    actual_version = str(methodology_payload.get("registry_version") or "")
    if declared_version != actual_version:
        findings.append(
            IntegrityFinding(
                "methodology",
                "versão do registro metodológico divergente: "
                f"declarada={declared_version!r}, real={actual_version!r}",
            )
        )

    unexpected_pending = sorted(set(pending) - ALLOWED_PENDING_METHODOLOGIES)
    for indicator_id in unexpected_pending:
        findings.append(IntegrityFinding("methodology", f"metodologia ausente: {indicator_id}"))
    for indicator_id in sorted(methodology_ids - canonical_ids):
        findings.append(IntegrityFinding("methodology", f"metodologia órfã: {indicator_id}"))

    for definition in registry.indicators:
        indicator_id = str(definition["indicator_id"])
        expected_reference = f"methodology_registry.json#{indicator_id}"
        if str(definition["methodology_reference"]) != expected_reference:
            findings.append(
                IntegrityFinding(
                    "methodology",
                    f"referência metodológica inválida: {indicator_id}",
                )
            )
        methodology = methodologies.get(indicator_id)
        if methodology and str(methodology.get("indicator_version")) != str(definition["indicator_version"]):
            findings.append(
                IntegrityFinding(
                    "methodology",
                    f"versão de indicador divergente na metodologia: {indicator_id}",
                )
            )
    return pending, tuple(findings)


def _interface_findings(root: Path) -> tuple[IntegrityFinding, ...]:
    text = (root / INTERFACE_PATH).read_text(encoding="utf-8")
    findings = [
        IntegrityFinding("interface", f"token canônico ausente: {token}")
        for token in INTERFACE_CONTRACT_TOKENS
        if token not in text
    ]
    if 'metric("Versão do catálogo", "1.0.0")' in text:
        findings.append(IntegrityFinding("interface", "versão fixa do registro detectada"))
    return tuple(findings)


def audit_scientific_integrity(repository_root: str | Path) -> ScientificIntegrityReport:
    root = Path(repository_root).resolve()
    registry = load_indicator_registry(root)
    methodology_payload = _methodology_payload(root)
    methodologies = _methodologies(methodology_payload)
    engine_registry = default_indicator_registry()
    implementations = tuple(engine_registry)
    findings: list[IntegrityFinding] = []

    reference_report = audit_reference_corpus_manifest(root)
    findings.extend(
        IntegrityFinding(
            "reference_corpus_manifest",
            f"{item.field}: {item.message}",
        )
        for item in reference_report.findings
    )

    if (root / LEGACY_CATALOG_PATH).exists():
        findings.append(IntegrityFinding("single_source", "catálogo legado voltou ao repositório"))

    for duplicate in find_duplicate_definitions(root):
        findings.append(
            IntegrityFinding(
                "single_source",
                f"{duplicate.path}: {duplicate.indicator_id}.{duplicate.field}",
            )
        )

    findings.extend(_implementation_findings(registry))
    pending, methodology_findings = _methodology_findings(
        registry,
        methodology_payload,
        methodologies,
    )
    findings.extend(methodology_findings)

    methodology_report = audit_methodologies(
        methodologies.values(),
        engine_registry,
    )
    findings.extend(
        IntegrityFinding(
            "methodology_consistency",
            f"{item.indicator_id}.{item.rule}: {item.message}",
        )
        for item in methodology_report.findings
    )
    findings.extend(_interface_findings(root))

    return ScientificIntegrityReport(
        registry_version=registry.version,
        indicator_count=len(registry.indicators),
        implementation_count=len(implementations),
        methodology_count=len(methodologies),
        pending_methodologies=pending,
        findings=tuple(findings),
    )


def assert_scientific_integrity(report: ScientificIntegrityReport) -> None:
    if report.findings:
        details = "; ".join(
            f"[{finding.contract}] {finding.message}" for finding in report.findings
        )
        raise ValueError(details)
