"""Executa a auditoria de infraestrutura digital dos corpora ativos.

Modos:
    legacy  - mantém as saídas CSV e JSON existentes (padrão).
    preview - adapta e valida sem persistir no ledger.
    ledger  - preserva artefatos, cria manifesto e persiste no núcleo.

Exemplos:
    python scripts/audit_digital_infrastructure.py
    python scripts/audit_digital_infrastructure.py --mode preview --snapshot-id snapshot_2026_q3 --limit 5
    python scripts/audit_digital_infrastructure.py --mode ledger --snapshot-id snapshot_2026_q3 --corpus europeana ina
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
from memoria_audiovisual.statetech.digital_infrastructure_adapter import (
    DigitalInfrastructureAuditAdapter,
)
from memoria_audiovisual.statetech.ingestion import IngestionCoordinator, IngestionResult
from memoria_audiovisual.statetech.ingestion_batches import BatchManifestStore
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.raw_artifacts import RawArtifactStore
from memoria_audiovisual.statetech.service import StatetechDataService

OUTPUT_DIR = BASE_DIR / "data" / "output"
STATE_DIR = BASE_DIR / "data" / "statetech"
CSV_FILENAME = "digital_infrastructure_audit.csv"
JSON_FILENAME = "digital_infrastructure_audit.json"
DEFAULT_LEDGER = STATE_DIR / "ledger.jsonl"
DEFAULT_ARTIFACT_DIR = STATE_DIR / "raw_artifacts"
DEFAULT_BATCH_MANIFEST = STATE_DIR / "ingestion_batches.jsonl"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mapeia CMS, APIs, metadados, interoperabilidade, busca, restrições e sinais públicos de IA."
    )
    parser.add_argument(
        "--mode",
        choices=("legacy", "preview", "ledger"),
        default="legacy",
        help="Modo de saída. O padrão legacy preserva o comportamento histórico.",
    )
    parser.add_argument(
        "--snapshot-id",
        default=None,
        help="Identificador do snapshot, obrigatório nos modos preview e ledger.",
    )
    parser.add_argument(
        "--corpus",
        nargs="*",
        help="Códigos de corpora específicos. Sem esta opção, audita todos os corpora ativos.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de corpora auditados.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout HTTP por URL, em segundos.")
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Inclui unidades que não estejam marcadas como organism_active.",
    )
    parser.add_argument("--ledger-path", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--batch-manifest", type=Path, default=DEFAULT_BATCH_MANIFEST)
    parser.add_argument(
        "--result-output",
        type=Path,
        default=None,
        help="Arquivo JSON opcional para o resumo de preview ou ledger.",
    )
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
        result = audit_url(
            source_url,
            corpus_code=code,
            institution=label,
            timeout=timeout,
        )
        record = result.to_dict()
        record.update(
            {
                "category_code": corpus.get("category_code", ""),
                "entity_level": corpus.get("entity_level", "") or "corpus",
                "coverage_level": corpus.get("coverage_level", ""),
                "collection_completeness": corpus.get("collection_completeness", ""),
                "country": corpus.get("country"),
            }
        )
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
    ledger = AtomicLedger(args.ledger_path)
    service = StatetechDataService(ledger, registry)
    if args.mode == "ledger":
        return IngestionCoordinator(
            service,
            artifact_store=RawArtifactStore(args.artifact_dir),
            batch_store=BatchManifestStore(args.batch_manifest),
        )
    return IngestionCoordinator(service)


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
        if args.mode == "preview":
            result = active_coordinator.preview(adapter, record)
        else:
            result = active_coordinator.commit(adapter, record)
        results.append(result)

    payload = {
        "mode": args.mode,
        "snapshot_id": args.snapshot_id,
        "source_count": len(records),
        "record_count": sum(result.record_count for result in results),
        "committed_count": sum(result.committed_count for result in results),
        "resumed_count": sum(result.resumed_count for result in results),
        "batches": [
            {
                "adapter_name": result.adapter_name,
                "adapter_version": result.adapter_version,
                "batch_id": result.batch_id,
                "source_artifact_id": result.source_artifact_id,
                "record_count": result.record_count,
                "committed_count": result.committed_count,
                "resumed_count": result.resumed_count,
                "items": [asdict(item) for item in result.items],
            }
            for result in results
        ],
    }
    if args.result_output:
        args.result_output.parent.mkdir(parents=True, exist_ok=True)
        args.result_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    corpora = select_corpora(args)
    records = collect_records(corpora, timeout=args.timeout)
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
        f"{summary['record_count']} observações normalizadas; "
        f"{summary['committed_count']} novos commits; "
        f"{summary['resumed_count']} recuperados."
    )
    if args.result_output:
        print(f"Resumo: {args.result_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
