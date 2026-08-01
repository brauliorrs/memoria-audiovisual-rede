"""Executa a auditoria de infraestrutura digital dos corpora ativos.

Modos:
    legacy  - mantém as saídas CSV e JSON existentes (padrão).
    preview - adapta, valida e gera cobertura sem persistir no ledger.
    ledger  - preserva artefatos, cria manifesto, persiste e salva relatórios.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure_audit import audit_url
from memoria_audiovisual.statetech.contracts import SchemaRegistry
from memoria_audiovisual.statetech.coverage_reports import (
    CoverageReportStore,
    observations_from_ingestion_payload,
)
from memoria_audiovisual.statetech.digital_infrastructure_adapter import (
    DigitalInfrastructureAuditAdapter,
)
from memoria_audiovisual.statetech.ingestion import IngestionCoordinator, IngestionResult
from memoria_audiovisual.statetech.ingestion_batches import BatchManifestStore
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.parameter_coverage import build_coverage_matrix
from memoria_audiovisual.statetech.raw_artifacts import RawArtifactStore
from memoria_audiovisual.statetech.service import StatetechDataService

OUTPUT_DIR = BASE_DIR / "data" / "output"
STATE_DIR = BASE_DIR / "data" / "statetech"
CSV_FILENAME = "digital_infrastructure_audit.csv"
JSON_FILENAME = "digital_infrastructure_audit.json"
DEFAULT_LEDGER = STATE_DIR / "ledger.jsonl"
DEFAULT_ARTIFACT_DIR = STATE_DIR / "raw_artifacts"
DEFAULT_BATCH_MANIFEST = STATE_DIR / "ingestion_batches.jsonl"
DEFAULT_COVERAGE_DIR = STATE_DIR / "coverage"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mapeia CMS, APIs, metadados, interoperabilidade, busca, restrições e sinais públicos de IA."
    )
    parser.add_argument("--mode", choices=("legacy", "preview", "ledger"), default="legacy")
    parser.add_argument("--snapshot-id", default=None)
    parser.add_argument("--corpus", nargs="*")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--include-inactive", action="store_true")
    parser.add_argument("--ledger-path", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--batch-manifest", type=Path, default=DEFAULT_BATCH_MANIFEST)
    parser.add_argument("--coverage-dir", type=Path, default=DEFAULT_COVERAGE_DIR)
    parser.add_argument(
        "--write-coverage",
        action="store_true",
        help="No preview, permite salvar os relatórios derivados sem gravar no ledger.",
    )
    parser.add_argument("--result-output", type=Path, default=None)
    args = parser.parse_args(argv)
    if args.mode != "legacy" and not str(args.snapshot_id or "").strip():
        parser.error("--snapshot-id é obrigatório nos modos preview e ledger")
    return args


def select_corpora(args: argparse.Namespace) -> list[dict[str, Any]]:
    requested = set(args.corpus or [])
    unknown = sorted(requested.difference(CORPORA))
    if unknown:
        raise SystemExit(f"Corpora desconhecidos: {', '.join(unknown)}")
    selected: list[dict[str, Any]] = []
    for code, corpus in CORPORA.items():
        if requested and code not in requested:
            continue
        if not args.include_inactive and not corpus.get("organism_active", False):
            continue
        if not corpus.get("source_url"):
            continue
        selected.append(dict(corpus))
    selected.sort(key=lambda item: (item.get("expansion_priority", 999), item.get("label", "")))
    return selected[: args.limit] if args.limit else selected


def collect_records(corpora: list[dict[str, Any]], *, timeout: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for position, corpus in enumerate(corpora, start=1):
        code = str(corpus["code"])
        label = str(corpus["label"])
        source_url = str(corpus["source_url"])
        print(f"[{position}/{len(corpora)}] {code}: {source_url}")
        result = audit_url(source_url, corpus_code=code, institution=label, timeout=timeout)
        record = result.to_dict()
        record.update({
            "category_code": corpus.get("category_code", ""),
            "entity_level": corpus.get("entity_level", "") or "corpus",
            "coverage_level": corpus.get("coverage_level", ""),
            "collection_completeness": corpus.get("collection_completeness", ""),
            "country": corpus.get("country"),
        })
        records.append(record)
    return records


def write_legacy_outputs(records: list[dict[str, Any]]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    dataframe = pd.DataFrame(records)
    csv_path = OUTPUT_DIR / CSV_FILENAME
    json_path = OUTPUT_DIR / JSON_FILENAME
    dataframe.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    return csv_path, json_path


def build_coordinator(args: argparse.Namespace) -> IngestionCoordinator:
    registry = SchemaRegistry(BASE_DIR)
    service = StatetechDataService(AtomicLedger(args.ledger_path), registry)
    if args.mode == "ledger":
        return IngestionCoordinator(
            service,
            artifact_store=RawArtifactStore(args.artifact_dir),
            batch_store=BatchManifestStore(args.batch_manifest),
        )
    return IngestionCoordinator(service)


def build_coverage_payload(
    ingestion_payload: dict[str, Any], *, corpus_codes: list[str], snapshot_id: str
) -> dict[str, Any]:
    observations = observations_from_ingestion_payload(ingestion_payload)
    coverage = tuple(
        item
        for corpus_code in corpus_codes
        for item in build_coverage_matrix(
            observations, corpus_code=corpus_code, snapshot_id=snapshot_id
        )
    )
    status_counts: dict[str, int] = {}
    for item in coverage:
        status_counts[item.status] = status_counts.get(item.status, 0) + 1
    return {
        "snapshot_id": snapshot_id,
        "corpus_count": len(corpus_codes),
        "parameter_count": len(coverage),
        "status_counts": status_counts,
        "items": [item.to_dict() for item in coverage],
        "_coverage_objects": coverage,
    }


def persist_coverage_if_enabled(payload: dict[str, Any], *, args: argparse.Namespace) -> dict[str, Any] | None:
    if args.mode != "ledger" and not args.write_coverage:
        return None
    coverage_payload = payload["coverage"]
    store = CoverageReportStore(args.coverage_dir)
    previous = store.latest_manifest(exclude_snapshot_id=str(args.snapshot_id))
    manifest = store.write(
        snapshot_id=str(args.snapshot_id),
        coverage=coverage_payload["_coverage_objects"],
        previous_manifest=previous,
    )
    return manifest.to_dict()


def run_statetech_mode(
    records: list[dict[str, Any]],
    *,
    args: argparse.Namespace,
    coordinator: IngestionCoordinator | None = None,
) -> dict[str, Any]:
    if args.mode not in {"preview", "ledger"}:
        raise ValueError("run_statetech_mode exige preview ou ledger")
    active_coordinator = coordinator or build_coordinator(args)
    results: list[IngestionResult] = []
    for record in records:
        adapter = DigitalInfrastructureAuditAdapter(
            snapshot_id=str(args.snapshot_id),
            entity_level=str(record.get("entity_level") or "corpus"),
        )
        result = (
            active_coordinator.preview(adapter, record)
            if args.mode == "preview"
            else active_coordinator.commit(adapter, record)
        )
        results.append(result)

    payload: dict[str, Any] = {
        "mode": args.mode,
        "snapshot_id": args.snapshot_id,
        "source_count": len(records),
        "record_count": sum(result.record_count for result in results),
        "committed_count": sum(result.committed_count for result in results),
        "resumed_count": sum(result.resumed_count for result in results),
        "batches": [{
            "adapter_name": result.adapter_name,
            "adapter_version": result.adapter_version,
            "batch_id": result.batch_id,
            "source_artifact_id": result.source_artifact_id,
            "record_count": result.record_count,
            "committed_count": result.committed_count,
            "resumed_count": result.resumed_count,
            "items": [asdict(item) for item in result.items],
        } for result in results],
    }
    corpus_codes = [str(record.get("corpus_code") or "") for record in records]
    payload["coverage"] = build_coverage_payload(
        payload, corpus_codes=corpus_codes, snapshot_id=str(args.snapshot_id)
    )
    manifest = persist_coverage_if_enabled(payload, args=args)
    if manifest:
        payload["coverage_manifest"] = manifest

    payload["coverage"].pop("_coverage_objects", None)
    if args.result_output:
        args.result_output.parent.mkdir(parents=True, exist_ok=True)
        args.result_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    records = collect_records(select_corpora(args), timeout=args.timeout)
    reachable = sum(bool(record.get("reachable")) for record in records)
    if args.mode == "legacy":
        csv_path, json_path = write_legacy_outputs(records)
        print(f"Auditoria concluída: {len(records)} unidades; {reachable} superfícies alcançáveis.")
        print(f"CSV: {csv_path}")
        print(f"JSON: {json_path}")
        return 0

    summary = run_statetech_mode(records, args=args)
    print(
        f"Modo {args.mode}: {summary['source_count']} fontes; "
        f"{summary['record_count']} observações; "
        f"{summary['coverage']['parameter_count']} estados de cobertura; "
        f"{summary['committed_count']} novos commits."
    )
    if summary.get("coverage_manifest"):
        print(f"Cobertura: {summary['coverage_manifest']['coverage_path']}")
        if summary['coverage_manifest'].get('changes_path'):
            print(f"Mudanças: {summary['coverage_manifest']['changes_path']}")
    if args.result_output:
        print(f"Resumo: {args.result_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
