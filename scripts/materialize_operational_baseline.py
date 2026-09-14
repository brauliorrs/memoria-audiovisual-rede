#!/usr/bin/env python3
"""Valida e materializa o manifesto do primeiro baseline operacional oficial."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from memoria_audiovisual.analytics.storage import AnalyticsStore

AI_FLAG_NAMES = (
    "MAR_AI_EXPERIMENTS_ENABLED",
    "MAR_AI_INSTITUTIONAL_USE_ENABLED",
    "MAR_AI_COLLECTION_DETECTION_ENABLED",
    "MAR_AI_VIDEO_PRESENCE_ENABLED",
    "MAR_AI_SYNTHETIC_VIDEO_ENABLED",
)
FALSE_VALUES = {"", "0", "false", "no", "off"}


def utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"artefato ausente: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"objeto JSON esperado: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"log JSONL ausente: {path}")
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"JSONL inválido em {path}:{line_number}") from exc
            if not isinstance(item, dict):
                raise ValueError(f"registro JSONL inválido em {path}:{line_number}")
            rows.append(item)
    if not rows:
        raise ValueError(f"log JSONL vazio: {path}")
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ai_flags_are_disabled() -> tuple[bool, dict[str, str]]:
    values = {name: str(os.environ.get(name, "")).strip() for name in AI_FLAG_NAMES}
    enabled = {
        name: value
        for name, value in values.items()
        if value.lower() not in FALSE_VALUES
    }
    return not enabled, values


def validate_t1_gate(path: Path, *, expected_corpora: int) -> dict[str, Any]:
    gate = load_json(path)
    if gate.get("gate") != "t1_auditable_completion":
        raise ValueError("artefato T1 não declara o portão de conclusão auditável")
    if gate.get("auditable_completion") is not True:
        raise ValueError("T1 não está marcado como auditavelmente concluído")
    if int(gate.get("active_corpora_total") or 0) != expected_corpora:
        raise ValueError("denominador ativo do T1 diverge do baseline operacional")
    if int(gate.get("recorded_results_total") or 0) != expected_corpora:
        raise ValueError("T1 não registra resultado para todos os corpora ativos")
    return gate


def materialize(
    *,
    snapshot_id: str,
    t1_gate_path: Path,
    audit_summary_path: Path,
    analytics_root: Path,
    ledger_path: Path,
    batch_manifest_path: Path,
    output_path: Path,
    expected_corpora: int,
    expected_parameters: int,
    expected_indicators: int,
    pipeline_commit: str,
) -> dict[str, Any]:
    ai_disabled, ai_flag_values = ai_flags_are_disabled()
    if not ai_disabled:
        enabled = [name for name, value in ai_flag_values.items() if value.lower() not in FALSE_VALUES]
        raise ValueError(
            "o baseline oficial exige todas as flags experimentais de IA desligadas: "
            + ", ".join(enabled)
        )

    t1_gate = validate_t1_gate(t1_gate_path, expected_corpora=expected_corpora)
    audit = load_json(audit_summary_path)
    if audit.get("mode") != "ledger":
        raise ValueError("a auditoria operacional deve executar em modo ledger")
    if str(audit.get("snapshot_id") or "") != snapshot_id:
        raise ValueError("snapshot_id do resumo de auditoria diverge do solicitado")
    if int(audit.get("source_count") or 0) != expected_corpora:
        raise ValueError("quantidade de fontes da auditoria diverge do corpus ativo")

    batches = audit.get("batches") or []
    if not isinstance(batches, list) or len(batches) != expected_corpora:
        raise ValueError("a auditoria deve registrar exatamente um lote por corpus ativo")
    batch_ids = [str(item.get("batch_id") or "") for item in batches]
    if any(not batch_id for batch_id in batch_ids) or len(set(batch_ids)) != len(batch_ids):
        raise ValueError("lotes da auditoria possuem identificadores vazios ou duplicados")

    coverage = audit.get("coverage") or {}
    if int(coverage.get("corpus_count") or 0) != expected_corpora:
        raise ValueError("cobertura não contém todos os corpora ativos")
    if int(coverage.get("parameter_count") or 0) != expected_parameters:
        raise ValueError("quantidade de estados de cobertura diverge do contrato")

    coverage_manifest = audit.get("coverage_manifest") or {}
    coverage_path = Path(str(coverage_manifest.get("coverage_path") or ""))
    if not coverage_path.exists():
        raise FileNotFoundError(f"matriz de cobertura ausente: {coverage_path}")

    snapshot_root = analytics_root / snapshot_id
    indicators_path = snapshot_root / "snapshot_indicators.json"
    analytics_manifest_path = snapshot_root / "manifest.json"
    run_path = snapshot_root / "run.json"
    sensitivity_path = snapshot_root / "interoperability_sensitivity.json"
    indicators = load_json(indicators_path)
    run = load_json(run_path)
    load_json(sensitivity_path)
    verified_manifest = AnalyticsStore(analytics_root).verify(snapshot_id)

    if indicators.get("status") != "completed" or run.get("status") != "completed":
        raise ValueError("execução analítica não está concluída")
    if int(indicators.get("indicator_count") or 0) != expected_indicators:
        raise ValueError("quantidade de indicadores materializados diverge do contrato")
    if len(indicators.get("results") or []) != expected_indicators:
        raise ValueError("lista de resultados analíticos incompleta")
    if int(run.get("indicator_count") or 0) != expected_indicators:
        raise ValueError("run.json diverge da quantidade esperada de indicadores")
    if verified_manifest.indicator_count != expected_indicators:
        raise ValueError("manifesto analítico diverge da quantidade esperada de indicadores")

    ledger_rows = read_jsonl(ledger_path)
    transaction_ids = [str(row.get("transaction_id") or "") for row in ledger_rows]
    if any(not transaction_id for transaction_id in transaction_ids):
        raise ValueError("ledger contém transação sem identificador")
    if len(transaction_ids) != len(set(transaction_ids)):
        raise ValueError("ledger contém transaction_id duplicado")
    ledger_record_count = 0
    for row in ledger_rows:
        records = row.get("records")
        if not isinstance(records, list) or not records:
            raise ValueError("ledger contém transação sem registros")
        ledger_record_count += len(records)

    batch_rows = read_jsonl(batch_manifest_path)
    latest_batches: dict[str, dict[str, Any]] = {}
    for row in batch_rows:
        batch_id = str(row.get("batch_id") or "")
        if not batch_id:
            raise ValueError("manifesto de lote contém batch_id vazio")
        latest_batches[batch_id] = row
    missing_batches = sorted(set(batch_ids) - set(latest_batches))
    if missing_batches:
        raise ValueError("lotes ausentes no manifesto append-only: " + ", ".join(missing_batches))
    incomplete_batches = sorted(
        batch_id
        for batch_id in batch_ids
        if latest_batches[batch_id].get("status") != "completed"
    )
    if incomplete_batches:
        raise ValueError("lotes não concluídos: " + ", ".join(incomplete_batches))

    artifact_paths = {
        "t1_gate": t1_gate_path,
        "audit_summary": audit_summary_path,
        "coverage": coverage_path,
        "snapshot_indicators": indicators_path,
        "analytics_manifest": analytics_manifest_path,
        "analytics_run": run_path,
        "interoperability_sensitivity": sensitivity_path,
        "indicator_history": analytics_root / "indicator_history.jsonl",
        "ledger": ledger_path,
        "ingestion_batches": batch_manifest_path,
    }
    for name, path in artifact_paths.items():
        if not path.exists():
            raise FileNotFoundError(f"artefato operacional ausente ({name}): {path}")

    manifest = {
        "schema_version": "1.0.0",
        "baseline_id": snapshot_id,
        "baseline_type": "operational_official",
        "status": "completed",
        "official_baseline": True,
        "generated_at": utcnow_iso(),
        "pipeline_commit": pipeline_commit,
        "t1_gate": {
            "source_run_id": t1_gate.get("source_run_id"),
            "source_manifest_sha256": t1_gate.get("source_manifest_sha256"),
            "auditable_completion": True,
            "recorded_results_total": expected_corpora,
        },
        "counts": {
            "active_corpora": expected_corpora,
            "coverage_parameters": expected_parameters,
            "indicators": expected_indicators,
            "ledger_transactions": len(ledger_rows),
            "ledger_records": ledger_record_count,
            "ingestion_batches": len(batch_ids),
            "successful_t1_corpora": int(t1_gate.get("successful_corpora_total") or 0),
            "non_successful_t1_corpora": int(t1_gate.get("non_successful_corpora_total") or 0),
        },
        "integrity": {
            "all_active_corpora_covered": True,
            "all_ingestion_batches_completed": True,
            "analytics_manifest_verified": True,
            "append_only_indicator_history_present": True,
            "append_only_ledger_present": True,
            "append_only_batch_history_present": True,
        },
        "ai": {
            "experimental_flags": ai_flag_values,
            "all_experimental_flags_disabled": True,
            "is_official_baseline_dependency": False,
            "synthetic_video_detection_enabled": False,
        },
        "artifacts": {
            name: {"path": str(path), "sha256": sha256_file(path)}
            for name, path in artifact_paths.items()
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(f"manifesto operacional já existe: {output_path}")
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--t1-gate", required=True, type=Path)
    parser.add_argument("--audit-summary", required=True, type=Path)
    parser.add_argument("--analytics-root", required=True, type=Path)
    parser.add_argument("--ledger-path", required=True, type=Path)
    parser.add_argument("--batch-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expected-corpora", type=int, default=55)
    parser.add_argument("--expected-parameters", type=int, default=385)
    parser.add_argument("--expected-indicators", type=int, default=9)
    parser.add_argument("--pipeline-commit", default="unknown")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = materialize(
        snapshot_id=args.snapshot_id,
        t1_gate_path=args.t1_gate,
        audit_summary_path=args.audit_summary,
        analytics_root=args.analytics_root,
        ledger_path=args.ledger_path,
        batch_manifest_path=args.batch_manifest,
        output_path=args.output,
        expected_corpora=args.expected_corpora,
        expected_parameters=args.expected_parameters,
        expected_indicators=args.expected_indicators,
        pipeline_commit=args.pipeline_commit,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
