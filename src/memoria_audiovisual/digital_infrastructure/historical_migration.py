"""Preparação e validação de migração histórica sem persistência.

O módulo lê CSV/JSON legados, normaliza valores escalares e produz um relatório
de compatibilidade. Nenhum registro é gravado no ledger.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

REQUIRED_SOURCE_FIELDS = ("corpus_code", "institution", "source_url", "reachable")
SIGNAL_FIELDS = (
    "cms", "api_types", "metadata_formats", "interoperability_protocols",
    "search_mechanisms", "access_restrictions", "ai_cataloguing_evidence",
)


@dataclass(frozen=True, slots=True)
class MigrationIssue:
    row_number: int
    severity: str
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class MigrationRowAssessment:
    row_number: int
    natural_key: str | None
    status: str
    missing_fields: tuple[str, ...] = ()
    signal_count: int = 0


@dataclass(frozen=True, slots=True)
class MigrationReport:
    source_path: str
    source_format: str
    total_rows: int
    compatible_rows: int
    review_required_rows: int
    blocked_rows: int
    duplicate_keys: tuple[str, ...]
    unknown_fields: tuple[str, ...]
    issues: tuple[MigrationIssue, ...]
    rows: tuple[MigrationRowAssessment, ...]
    dry_run: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HistoricalMigrationAnalyzer:
    """Analisa arquivos históricos e nunca persiste no núcleo."""

    def load(self, source: str | Path) -> list[dict[str, Any]]:
        path = Path(source)
        suffix = path.suffix.casefold()
        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError("o JSON histórico deve conter uma lista de objetos")
            return [dict(item) for item in payload]
        if suffix == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        raise ValueError("o arquivo histórico deve ser .csv ou .json")

    def analyze(self, source: str | Path) -> MigrationReport:
        path = Path(source)
        records = self.load(path)
        known = set(REQUIRED_SOURCE_FIELDS) | set(SIGNAL_FIELDS) | {
            "institution_name", "observed_at", "status_code", "final_url",
            "error", "category_code", "entity_level", "coverage_level",
            "collection_completeness",
        }
        unknown_fields = sorted({key for row in records for key in row if key not in known})
        issues: list[MigrationIssue] = []
        assessments: list[MigrationRowAssessment] = []
        seen: dict[str, int] = {}
        duplicates: set[str] = set()

        for number, raw in enumerate(records, start=1):
            row = self._normalize(raw)
            missing = tuple(field for field in REQUIRED_SOURCE_FIELDS if not str(row.get(field, "")).strip())
            corpus = str(row.get("corpus_code") or "").strip()
            source_url = str(row.get("source_url") or "").strip()
            natural_key = f"{corpus}|{source_url}" if corpus and source_url else None
            if natural_key:
                if natural_key in seen:
                    duplicates.add(natural_key)
                    issues.append(MigrationIssue(number, "error", "MIG-003", f"chave histórica duplicada; primeira ocorrência na linha {seen[natural_key]}"))
                else:
                    seen[natural_key] = number

            signal_count = sum(bool(self._values(row.get(field))) for field in SIGNAL_FIELDS)
            if missing:
                issues.append(MigrationIssue(number, "error", "MIG-001", f"campos obrigatórios ausentes: {', '.join(missing)}"))
                status = "blocked"
            elif natural_key in duplicates:
                status = "blocked"
            elif signal_count == 0:
                issues.append(MigrationIssue(number, "warning", "MIG-002", "registro sem sinais tecnológicos migráveis"))
                status = "review_required"
            else:
                status = "compatible"
            assessments.append(MigrationRowAssessment(number, natural_key, status, missing, signal_count))

        # Reclassifica também a primeira ocorrência de cada duplicidade.
        assessments = [
            MigrationRowAssessment(item.row_number, item.natural_key, "blocked" if item.natural_key in duplicates else item.status, item.missing_fields, item.signal_count)
            for item in assessments
        ]
        for field in unknown_fields:
            issues.append(MigrationIssue(0, "warning", "MIG-004", "campo não reconhecido será preservado apenas no artefato bruto", field))

        return MigrationReport(
            source_path=str(path),
            source_format=path.suffix.casefold().lstrip("."),
            total_rows=len(records),
            compatible_rows=sum(item.status == "compatible" for item in assessments),
            review_required_rows=sum(item.status == "review_required" for item in assessments),
            blocked_rows=sum(item.status == "blocked" for item in assessments),
            duplicate_keys=tuple(sorted(duplicates)),
            unknown_fields=tuple(unknown_fields),
            issues=tuple(issues),
            rows=tuple(assessments),
        )

    @staticmethod
    def _normalize(row: Mapping[str, Any]) -> dict[str, Any]:
        result = {str(key).strip(): value for key, value in row.items()}
        if not result.get("institution") and result.get("institution_name"):
            result["institution"] = result["institution_name"]
        return result

    @staticmethod
    def _values(value: Any) -> tuple[str, ...]:
        if value is None:
            return ()
        if isinstance(value, (list, tuple, set)):
            return tuple(str(item).strip() for item in value if str(item).strip())
        text = str(value).strip()
        if not text or text.casefold() in {"nan", "none", "null", "[]"}:
            return ()
        if text.startswith("["):
            try:
                parsed = json.loads(text.replace("'", '"'))
                if isinstance(parsed, list):
                    return tuple(str(item).strip() for item in parsed if str(item).strip())
            except json.JSONDecodeError:
                pass
        return tuple(item.strip() for item in text.replace(";", "|").split("|") if item.strip())
