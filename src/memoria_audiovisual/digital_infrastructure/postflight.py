"""Validação semântica de uma rodada infraestrutura digital concluída.

O pós-flight é executado depois da ingestão e antes da consolidação na branch
histórica. Ele não modifica o ledger nem os relatórios analisados.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

from .models import utc_now_iso
from .parameter_coverage import EXPECTED_DETECTOR_GROUPS


@dataclass(frozen=True, slots=True)
class PostflightIssue:
    code: str
    severity: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PostflightReport:
    snapshot_id: str
    ok: bool
    checked_at: str
    corpus_count: int
    coverage_row_count: int
    observation_count: int
    issues: tuple[PostflightIssue, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["issues"] = [issue.to_dict() for issue in self.issues]
        return payload


def _load_json(path: Path, *, expected_type: type) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"arquivo ausente: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {path}") from exc
    if not isinstance(payload, expected_type):
        raise ValueError(f"estrutura inválida em {path}: esperado {expected_type.__name__}")
    return payload


def _read_jsonl(path: Path) -> tuple[dict[str, Any], ...]:
    if not path.exists():
        raise ValueError(f"JSONL ausente: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL inválido em {path}:{line_number}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"linha não-objeto em {path}:{line_number}")
            rows.append(payload)
    return tuple(rows)


def validate_periodic_run(
    *,
    snapshot_id: str,
    state_dir: str | Path,
) -> PostflightReport:
    state = Path(state_dir)
    snapshot_dir = state / "coverage" / snapshot_id
    summary_path = snapshot_dir / "execution_summary.json"
    coverage_path = snapshot_dir / "parameter_coverage.json"
    index_path = state / "coverage" / "snapshot_coverage_index.jsonl"
    batch_path = state / "ingestion_batches.jsonl"
    ledger_path = state / "ledger.jsonl"

    issues: list[PostflightIssue] = []
    try:
        summary: Mapping[str, Any] = _load_json(summary_path, expected_type=dict)
        coverage: list[Mapping[str, Any]] = _load_json(coverage_path, expected_type=list)
        index_rows = _read_jsonl(index_path)
        batch_rows = _read_jsonl(batch_path)
        _read_jsonl(ledger_path)
    except ValueError as exc:
        issue = PostflightIssue("POST-001", "error", str(exc))
        return PostflightReport(snapshot_id, False, utc_now_iso(), 0, 0, 0, (issue,))

    if str(summary.get("snapshot_id") or "") != snapshot_id:
        issues.append(PostflightIssue(
            "POST-002", "error", "snapshot do resumo diverge do solicitado",
            {"summary_snapshot_id": summary.get("snapshot_id")},
        ))

    corpus_groups: dict[str, set[str]] = {}
    observation_total = 0
    for position, row in enumerate(coverage, start=1):
        corpus = str(row.get("corpus_code") or "").strip()
        row_snapshot = str(row.get("snapshot_id") or "").strip()
        group = str(row.get("detector_group") or "").strip()
        status = str(row.get("status") or "").strip()
        try:
            count = int(row.get("observation_count", 0))
        except (TypeError, ValueError):
            count = -1
        if not corpus or row_snapshot != snapshot_id or group not in EXPECTED_DETECTOR_GROUPS:
            issues.append(PostflightIssue(
                "POST-003", "error", "linha de cobertura inválida",
                {"position": position, "corpus_code": corpus, "snapshot_id": row_snapshot, "detector_group": group},
            ))
            continue
        corpus_groups.setdefault(corpus, set()).add(group)
        if status == "missing_observation":
            issues.append(PostflightIssue(
                "POST-004", "error", "grupo sem observação na rodada concluída",
                {"corpus_code": corpus, "detector_group": group},
            ))
        if count < 1:
            issues.append(PostflightIssue(
                "POST-005", "error", "cobertura sem observação associada",
                {"corpus_code": corpus, "detector_group": group, "observation_count": count},
            ))
        else:
            observation_total += count

    expected_groups = set(EXPECTED_DETECTOR_GROUPS)
    for corpus, groups in sorted(corpus_groups.items()):
        missing = sorted(expected_groups - groups)
        extra = sorted(groups - expected_groups)
        if missing or extra or len(groups) != len(EXPECTED_DETECTOR_GROUPS):
            issues.append(PostflightIssue(
                "POST-006", "error", "cobertura incompleta ou duplicada para o corpus",
                {"corpus_code": corpus, "missing_groups": missing, "extra_groups": extra, "group_count": len(groups)},
            ))

    source_count = int(summary.get("source_count") or 0)
    record_count = int(summary.get("record_count") or 0)
    committed_count = int(summary.get("committed_count") or 0)
    resumed_count = int(summary.get("resumed_count") or 0)
    batches = summary.get("batches", ())
    if not isinstance(batches, list):
        batches = []
        issues.append(PostflightIssue("POST-007", "error", "batches do resumo não é uma lista"))

    if source_count != len(corpus_groups):
        issues.append(PostflightIssue(
            "POST-008", "error", "quantidade de fontes diverge da cobertura",
            {"source_count": source_count, "coverage_corpus_count": len(corpus_groups)},
        ))
    if len(coverage) != len(corpus_groups) * len(EXPECTED_DETECTOR_GROUPS):
        issues.append(PostflightIssue(
            "POST-009", "error", "quantidade de linhas de cobertura diverge da matriz esperada",
            {"coverage_rows": len(coverage), "expected_rows": len(corpus_groups) * len(EXPECTED_DETECTOR_GROUPS)},
        ))
    if record_count != observation_total:
        issues.append(PostflightIssue(
            "POST-010", "error", "contagem de observações diverge entre resumo e cobertura",
            {"record_count": record_count, "coverage_observation_count": observation_total},
        ))
    if committed_count + resumed_count != record_count:
        issues.append(PostflightIssue(
            "POST-011", "error", "registros comprometidos e retomados não fecham o total",
            {"committed_count": committed_count, "resumed_count": resumed_count, "record_count": record_count},
        ))
    if len(batches) != source_count:
        issues.append(PostflightIssue(
            "POST-012", "error", "quantidade de lotes diverge da quantidade de fontes",
            {"batch_count": len(batches), "source_count": source_count},
        ))

    indexed = [row for row in index_rows if row.get("snapshot_id") == snapshot_id]
    if len(indexed) != 1:
        issues.append(PostflightIssue(
            "POST-013", "error", "snapshot deve aparecer exatamente uma vez no índice de cobertura",
            {"index_occurrences": len(indexed)},
        ))
    elif int(indexed[0].get("corpus_count") or 0) != len(corpus_groups) or int(indexed[0].get("parameter_count") or 0) != len(coverage):
        issues.append(PostflightIssue(
            "POST-014", "error", "manifesto de cobertura diverge dos relatórios",
            {"manifest": indexed[0], "corpus_count": len(corpus_groups), "parameter_count": len(coverage)},
        ))

    summary_batch_ids = {str(item.get("batch_id")) for item in batches if item.get("batch_id")}
    persisted_batch_ids = {str(row.get("batch_id")) for row in batch_rows if row.get("batch_id")}
    missing_batches = sorted(summary_batch_ids - persisted_batch_ids)
    if missing_batches:
        issues.append(PostflightIssue(
            "POST-015", "error", "lotes do resumo ausentes no manifesto persistido",
            {"missing_batch_ids": missing_batches},
        ))

    return PostflightReport(
        snapshot_id=snapshot_id,
        ok=not any(issue.severity == "error" for issue in issues),
        checked_at=utc_now_iso(),
        corpus_count=len(corpus_groups),
        coverage_row_count=len(coverage),
        observation_count=observation_total,
        issues=tuple(issues),
    )


def write_postflight_report(report: PostflightReport, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return output
