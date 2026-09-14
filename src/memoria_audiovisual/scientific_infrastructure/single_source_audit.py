"""Auditoria permanente da fonte única das definições científicas dos indicadores."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SEMANTIC_FIELDS = (
    "title",
    "scientific_question",
    "scientific_rationale",
    "selection_rationale",
    "interpretation",
    "relationship_to_other_indicators",
    "corpus_rule",
)
SCAN_ROOTS = ("app", "src", "scripts", "data")
TEXT_SUFFIXES = {".py", ".json", ".jsonl", ".yaml", ".yml", ".toml"}
EXCLUDED_PARTS = {"tests", "output", "__pycache__", ".git"}


@dataclass(frozen=True, slots=True)
class DuplicateDefinition:
    indicator_id: str
    field: str
    path: Path


def _semantic_values(registry_payload: dict) -> tuple[tuple[str, str, str], ...]:
    values: list[tuple[str, str, str]] = []
    for indicator in registry_payload.get("indicators", []):
        if not isinstance(indicator, dict):
            continue
        indicator_id = str(indicator.get("indicator_id", ""))
        for field in SEMANTIC_FIELDS:
            value = indicator.get(field)
            if isinstance(value, str) and len(value.strip()) >= 40:
                values.append((indicator_id, field, value.strip()))
    return tuple(values)


def find_duplicate_definitions(
    repository_root: Path,
    *,
    registry_relative_path: str = "data/templates/analytics/indicator_registry.json",
    scan_roots: Iterable[str] = SCAN_ROOTS,
) -> tuple[DuplicateDefinition, ...]:
    root = repository_root.resolve()
    registry_path = (root / registry_relative_path).resolve()
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    semantic_values = _semantic_values(registry_payload)
    findings: list[DuplicateDefinition] = []

    for relative_root in scan_roots:
        scan_root = root / relative_root
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if path.resolve() == registry_path or EXCLUDED_PARTS.intersection(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for indicator_id, field, value in semantic_values:
                if value in text:
                    findings.append(DuplicateDefinition(indicator_id, field, path.relative_to(root)))

    return tuple(findings)


def assert_single_source(findings: Iterable[DuplicateDefinition]) -> None:
    duplicates = tuple(findings)
    if not duplicates:
        return
    details = "; ".join(
        f"{item.path}: {item.indicator_id}.{item.field}" for item in duplicates
    )
    raise ValueError(f"Definições científicas duplicadas fora do registro canônico: {details}")
