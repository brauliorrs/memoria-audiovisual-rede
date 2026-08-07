"""Auditoria comparativa e executável das metodologias científicas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from memoria_audiovisual.analytics.registry import IndicatorRegistry as EngineRegistry

COMMON_REQUIRED_FIELDS = (
    "indicator_id",
    "indicator_version",
    "methodology_version",
    "definition",
    "formula",
    "source",
    "included_statuses",
    "excluded_statuses",
    "limitations",
)
EVALUABLE_STATUSES = frozenset({"detected", "not_detected", "unknown"})
NON_EVALUABLE_STATUSES = frozenset(
    {"error", "not_assessable", "missing_observation"}
)


@dataclass(frozen=True, slots=True)
class MethodologyFinding:
    indicator_id: str
    rule: str
    message: str


@dataclass(frozen=True, slots=True)
class MethodologyAuditReport:
    methodology_count: int
    complete_count: int
    methodology_classes: tuple[str, ...]
    findings: tuple[MethodologyFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _text(value: object) -> str:
    return str(value or "").strip()


def _string_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {_text(item) for item in value if _text(item)}


def _methodology_class(indicator_id: str, row: Mapping[str, Any]) -> str:
    if indicator_id == "audiovisual_archive_access_index":
        return "access"
    if indicator_id == "interoperability_index" or row.get("components"):
        return "composite_index"
    if indicator_id in {"dublin_core_coverage", "schema_org_coverage", "json_ld_coverage"}:
        return "metadata_coverage"
    if indicator_id in {"iiif_coverage", "oai_pmh_coverage", "interoperability_coverage"}:
        return "interoperability_coverage"
    return "infrastructure_coverage"


def _common_findings(row: Mapping[str, Any], position: int) -> list[MethodologyFinding]:
    indicator_id = _text(row.get("indicator_id")) or f"<posição {position}>"
    findings: list[MethodologyFinding] = []
    for field in COMMON_REQUIRED_FIELDS:
        value = row.get(field)
        if field in {"included_statuses", "excluded_statuses", "limitations"}:
            if not isinstance(value, list) or not value:
                findings.append(
                    MethodologyFinding(indicator_id, "completeness", f"{field} deve ser lista não vazia")
                )
        elif not _text(value):
            findings.append(
                MethodologyFinding(indicator_id, "completeness", f"{field} é obrigatório")
            )

    included = _string_set(row.get("included_statuses"))
    excluded = _string_set(row.get("excluded_statuses"))
    overlap = sorted(included & excluded)
    if overlap:
        findings.append(
            MethodologyFinding(
                indicator_id,
                "status_policy",
                f"estados simultaneamente incluídos e excluídos: {overlap}",
            )
        )
    if included != EVALUABLE_STATUSES:
        findings.append(
            MethodologyFinding(
                indicator_id,
                "status_policy",
                f"estados avaliáveis divergentes: {sorted(included)}",
            )
        )
    if excluded != NON_EVALUABLE_STATUSES:
        findings.append(
            MethodologyFinding(
                indicator_id,
                "status_policy",
                f"estados não avaliáveis divergentes: {sorted(excluded)}",
            )
        )
    return findings


def _composite_findings(row: Mapping[str, Any]) -> list[MethodologyFinding]:
    indicator_id = _text(row.get("indicator_id"))
    if indicator_id != "interoperability_index":
        return []
    findings: list[MethodologyFinding] = []
    components = row.get("components")
    if not isinstance(components, list) or not components:
        return [MethodologyFinding(indicator_id, "composite", "components deve ser lista não vazia")]

    weights: list[float] = []
    names: list[str] = []
    for component in components:
        if not isinstance(component, Mapping):
            findings.append(MethodologyFinding(indicator_id, "composite", "componente inválido"))
            continue
        names.append(_text(component.get("name")))
        weight = component.get("weight")
        if not isinstance(weight, (int, float)) or weight <= 0:
            findings.append(MethodologyFinding(indicator_id, "composite", "peso deve ser positivo"))
        else:
            weights.append(float(weight))
    if len(names) != len(set(names)):
        findings.append(MethodologyFinding(indicator_id, "composite", "componentes duplicados"))
    if weights and abs(sum(weights) - 1.0) > 1e-9:
        findings.append(
            MethodologyFinding(indicator_id, "composite", f"soma dos pesos deve ser 1.0, obtido {sum(weights):.6f}")
        )
    minimum = row.get("minimum_evaluable_components")
    if not isinstance(minimum, int) or minimum < 1 or minimum > len(components):
        findings.append(
            MethodologyFinding(indicator_id, "composite", "minimum_evaluable_components inválido")
        )
    if not _text(row.get("missing_data_policy")):
        findings.append(MethodologyFinding(indicator_id, "composite", "missing_data_policy é obrigatório"))
    return findings


def audit_methodologies(
    methodologies: Iterable[Mapping[str, Any]],
    engine_registry: EngineRegistry,
) -> MethodologyAuditReport:
    rows = tuple(methodologies)
    implementations = {item.indicator_id: item for item in engine_registry}
    findings: list[MethodologyFinding] = []
    classes: set[str] = set()
    complete_count = 0
    seen: set[str] = set()

    for position, row in enumerate(rows, start=1):
        indicator_id = _text(row.get("indicator_id")) or f"<posição {position}>"
        row_findings = _common_findings(row, position)
        row_findings.extend(_composite_findings(row))
        classes.add(_methodology_class(indicator_id, row))

        if indicator_id in seen:
            row_findings.append(MethodologyFinding(indicator_id, "identity", "metodologia duplicada"))
        seen.add(indicator_id)

        implementation = implementations.get(indicator_id)
        if implementation is None:
            row_findings.append(MethodologyFinding(indicator_id, "implementation", "sem implementação analítica"))
        else:
            if _text(row.get("indicator_version")) != implementation.version:
                row_findings.append(
                    MethodologyFinding(indicator_id, "version", "indicator_version diverge do motor")
                )
            if _text(row.get("methodology_version")) != implementation.methodology_version:
                row_findings.append(
                    MethodologyFinding(indicator_id, "version", "methodology_version diverge do motor")
                )
            formula = _text(row.get("formula"))
            if implementation.unit in {"percent", "score_0_100"} and "100" not in formula:
                row_findings.append(
                    MethodologyFinding(indicator_id, "formula", "fórmula não explicita escala 0–100")
                )

        if not row_findings:
            complete_count += 1
        findings.extend(row_findings)

    for indicator_id in sorted(set(implementations) - seen):
        findings.append(MethodologyFinding(indicator_id, "coverage", "implementação sem metodologia"))

    return MethodologyAuditReport(
        methodology_count=len(rows),
        complete_count=complete_count,
        methodology_classes=tuple(sorted(classes)),
        findings=tuple(findings),
    )


def assert_methodology_consistency(report: MethodologyAuditReport) -> None:
    if report.findings:
        details = "; ".join(
            f"{item.indicator_id}.{item.rule}: {item.message}" for item in report.findings
        )
        raise ValueError(details)
