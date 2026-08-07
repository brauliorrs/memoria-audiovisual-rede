"""Inventário científico derivado do corpus de referência canônico."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from memoria_audiovisual.corpora import CORPORA

MANIFEST_PATH = Path("data/reference_corpus/manifest.json")
INVENTORY_PATH = Path("data/reference_corpus/inventory.json")
CORE_FIELDS = (
    "code",
    "label",
    "category_code",
    "expansion_priority",
    "entity_level",
    "coverage_level",
    "scope",
    "methodological_unit",
    "organism_active",
    "monthly_refresh_enabled",
)


@dataclass(frozen=True, slots=True)
class InventoryFinding:
    field: str
    message: str


@dataclass(frozen=True, slots=True)
class ReferenceCorpusInventoryReport:
    total_entities: int
    active_entities: int
    inventory: Mapping[str, Any]
    findings: tuple[InventoryFinding, ...]

    @property
    def is_valid(self) -> bool:
        return not self.findings


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path}: raiz JSON deve ser objeto")
    return payload


def _counter(rows: list[Mapping[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(str(row.get(field, "__missing__")) for row in rows)
    return dict(sorted(counts.items()))


def build_reference_corpus_inventory(
    corpora: Mapping[str, Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    rows = [corpora[key] for key in sorted(corpora)]
    dataset = manifest.get("dataset") or {}
    reference = manifest.get("reference_corpus") or {}

    missing_by_field = {
        field: sum(
            1
            for row in rows
            if field not in row or row.get(field) in (None, "")
        )
        for field in CORE_FIELDS
    }

    active = sum(bool(row.get("organism_active")) for row in rows)
    monthly = sum(bool(row.get("monthly_refresh_enabled")) for row in rows)

    return {
        "inventory": {
            "inventory_id": "scientific_reference_corpus_inventory",
            "version": "1.0.0",
            "status": "derived",
            "reference_corpus_version": str(reference.get("version") or ""),
            "source_path": str(dataset.get("path") or ""),
            "source_selector": str(dataset.get("selector") or ""),
            "source_content_hash": str(dataset.get("content_hash") or ""),
        },
        "summary": {
            "total_entities": len(rows),
            "active_entities": active,
            "inactive_entities": len(rows) - active,
            "monthly_refresh_enabled": monthly,
            "monthly_refresh_disabled": len(rows) - monthly,
        },
        "distributions": {
            "category_code": _counter(rows, "category_code"),
        },
        "field_completeness": {
            "required_fields": list(CORE_FIELDS),
            "missing_values_by_field": missing_by_field,
            "complete_entities": sum(
                all(field in row and row.get(field) not in (None, "") for field in CORE_FIELDS)
                for row in rows
            ),
        },
        "governance": {
            "derived_from_canonical_source": True,
            "does_not_modify_corpus": True,
            "regenerable": True,
            "authoritative_for_corpus_membership": False,
        },
    }


def audit_reference_corpus_inventory(repository_root: str | Path) -> ReferenceCorpusInventoryReport:
    root = Path(repository_root).resolve()
    manifest_path = root / MANIFEST_PATH
    inventory_path = root / INVENTORY_PATH
    findings: list[InventoryFinding] = []

    if not manifest_path.exists():
        return ReferenceCorpusInventoryReport(
            0,
            0,
            {},
            (InventoryFinding("manifest", "manifesto ausente"),),
        )
    if not inventory_path.exists():
        return ReferenceCorpusInventoryReport(
            0,
            0,
            {},
            (InventoryFinding("inventory", "inventário derivado ausente"),),
        )

    manifest = _read_json(manifest_path)
    stored = _read_json(inventory_path)
    expected = build_reference_corpus_inventory(CORPORA, manifest)

    if stored != expected:
        findings.append(
            InventoryFinding(
                "inventory",
                "artefato derivado diverge da fonte canônica; regenere o inventário",
            )
        )

    summary = expected["summary"]
    manifest_entities = int((manifest.get("dataset") or {}).get("entities") or 0)
    if summary["total_entities"] != manifest_entities:
        findings.append(
            InventoryFinding(
                "summary.total_entities",
                f"inventário={summary['total_entities']}, manifesto={manifest_entities}",
            )
        )

    missing = expected["field_completeness"]["missing_values_by_field"]
    for field, count in missing.items():
        if count:
            findings.append(
                InventoryFinding(
                    f"field_completeness.{field}",
                    f"{count} unidade(s) sem valor estrutural obrigatório",
                )
            )

    return ReferenceCorpusInventoryReport(
        total_entities=int(summary["total_entities"]),
        active_entities=int(summary["active_entities"]),
        inventory=expected,
        findings=tuple(findings),
    )


def assert_reference_corpus_inventory(report: ReferenceCorpusInventoryReport) -> None:
    if report.findings:
        details = "; ".join(
            f"{finding.field}: {finding.message}" for finding in report.findings
        )
        raise ValueError(details)
