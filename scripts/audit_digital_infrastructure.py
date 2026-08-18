"""Executa a auditoria de infraestrutura digital dos corpora ativos.

A Porta 2 mantém as saídas legadas para compatibilidade e, em paralelo, produz
registros longos validados pelo contrato Estado–tecnologia, ledger append-only e
camadas distintas para dados brutos, curados e publicáveis.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

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
    curated_rows,
    publishable_rows,
)
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.service import StatetechDataService

OUTPUT_DIR = BASE_DIR / "data" / "output"
CSV_FILENAME = "digital_infrastructure_audit.csv"
JSON_FILENAME = "digital_infrastructure_audit.json"
RAW_CSV_FILENAME = "digital_infrastructure_audit_raw.csv"
RAW_JSON_FILENAME = "digital_infrastructure_audit_raw.json"
CURATED_CSV_FILENAME = "digital_infrastructure_audit_curated.csv"
CURATED_JSON_FILENAME = "digital_infrastructure_audit_curated.json"
PUBLISHABLE_CSV_FILENAME = "digital_infrastructure_audit_publishable.csv"
PUBLISHABLE_JSON_FILENAME = "digital_infrastructure_audit_publishable.json"
LEDGER_FILENAME = "digital_infrastructure_audit_ledger.jsonl"


def default_snapshot_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"infrastructure-{timestamp}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Mapeia CMS, APIs, metadados, interoperabilidade, busca, restrições e sinais públicos de IA."
    )
    parser.add_argument(
        "--corpus",
        nargs="*",
        help="Códigos de corpora específicos. Sem esta opção, audita todos os corpora ativos.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limita a quantidade de corpora auditados.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout HTTP por URL, em segundos.")
    parser.add_argument(
        "--snapshot-id",
        default=None,
        help="Identificador do snapshot. Se omitido, um identificador UTC é criado para a rodada.",
    )
    parser.add_argument(
        "--ledger-path",
        default=None,
        help="Caminho do ledger append-only. O padrão fica em data/output.",
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Inclui unidades que não estejam marcadas como organism_active.",
    )
    return parser.parse_args()


def select_corpora(args: argparse.Namespace) -> list[dict]:
    requested = set(args.corpus or [])
    unknown = sorted(requested.difference(CORPORA))
    if unknown:
        raise SystemExit(f"Corpora desconhecidos: {', '.join(unknown)}")

    selected = []
    for code, corpus in CORPORA.items():
        if requested and code not in requested:
            continue
        if not args.include_inactive and not corpus.get("organism_active", False):
            continue
        source_url = corpus.get("source_url")
        if not source_url:
            continue
        selected.append(corpus)

    selected.sort(key=lambda item: (item.get("expansion_priority", 999), item.get("label", "")))
    return selected[: args.limit] if args.limit else selected


def _write_table(rows: list[dict], csv_path: Path, json_path: Path, *, columns: list[str]) -> None:
    dataframe = pd.DataFrame(rows, columns=columns)
    dataframe.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    corpora = select_corpora(args)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    snapshot_id = args.snapshot_id or default_snapshot_id()
    ledger_path = Path(args.ledger_path) if args.ledger_path else OUTPUT_DIR / LEDGER_FILENAME
    if not ledger_path.is_absolute():
        ledger_path = BASE_DIR / ledger_path

    schemas = SchemaRegistry(BASE_DIR)
    ledger = AtomicLedger(ledger_path)
    service = StatetechDataService(ledger, schemas)
    adapter = DigitalInfrastructureAuditAdapter()

    legacy_records: list[dict] = []
    raw_rows: list[dict] = []
    code_commit_sha = os.environ.get("GITHUB_SHA", "").strip()

    for position, corpus in enumerate(corpora, start=1):
        code = corpus["code"]
        label = corpus["label"]
        source_url = corpus["source_url"]
        print(f"[{position}/{len(corpora)}] {code}: {source_url}")
        result = audit_url(
            source_url,
            corpus_code=code,
            institution=label,
            timeout=args.timeout,
        )
        record = result.to_dict()
        record.update(
            {
                "snapshot_id": snapshot_id,
                "country": corpus.get("country") or None,
                "category_code": corpus.get("category_code", ""),
                "entity_level": corpus.get("entity_level", "") or "institution",
                "coverage_level": corpus.get("coverage_level", ""),
                "collection_completeness": corpus.get("collection_completeness", ""),
                "code_commit_sha": code_commit_sha or None,
            }
        )
        legacy_records.append(record)

        for adapted in adapter.adapt(record):
            entity = service.register_entity(
                entity_type=adapted.entity_type,
                natural_key=adapted.natural_key,
                payload=adapted.payload,
                provenance=adapted.provenance,
                evidences=adapted.evidences,
                previous_version_id=adapted.previous_version_id,
                referenced_entity_ids=adapted.referenced_entity_ids,
            )
            raw_rows.append(dict(entity.payload))

    legacy_dataframe = pd.DataFrame(legacy_records)
    legacy_dataframe.to_csv(OUTPUT_DIR / CSV_FILENAME, index=False, encoding="utf-8-sig")
    (OUTPUT_DIR / JSON_FILENAME).write_text(
        json.dumps(legacy_records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    schema_columns = list(schemas.load("digital_infrastructure_audit").get("properties", {}).keys())
    extra_columns = sorted({key for row in raw_rows for key in row if key not in schema_columns})
    columns = [*schema_columns, *extra_columns]
    _write_table(
        raw_rows,
        OUTPUT_DIR / RAW_CSV_FILENAME,
        OUTPUT_DIR / RAW_JSON_FILENAME,
        columns=columns,
    )

    curated = curated_rows(raw_rows)
    _write_table(
        curated,
        OUTPUT_DIR / CURATED_CSV_FILENAME,
        OUTPUT_DIR / CURATED_JSON_FILENAME,
        columns=columns,
    )

    publishable = publishable_rows(raw_rows)
    _write_table(
        publishable,
        OUTPUT_DIR / PUBLISHABLE_CSV_FILENAME,
        OUTPUT_DIR / PUBLISHABLE_JSON_FILENAME,
        columns=columns,
    )

    reachable = int(legacy_dataframe["reachable"].sum()) if not legacy_dataframe.empty else 0
    print(
        f"Auditoria concluída: {len(legacy_dataframe)} unidades; {reachable} superfícies alcançáveis; "
        f"{len(raw_rows)} detecções normalizadas."
    )
    print(f"Snapshot: {snapshot_id}")
    print(f"Registros brutos: {OUTPUT_DIR / RAW_JSON_FILENAME}")
    print(f"Registros curados: {OUTPUT_DIR / CURATED_JSON_FILENAME} ({len(curated)})")
    print(f"Registros publicáveis: {OUTPUT_DIR / PUBLISHABLE_JSON_FILENAME} ({len(publishable)})")
    print(f"Ledger append-only: {ledger_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
