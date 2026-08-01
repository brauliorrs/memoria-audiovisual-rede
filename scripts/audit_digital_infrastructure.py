"""Executa a auditoria de infraestrutura digital dos corpora ativos.

Exemplos:
    python scripts/audit_digital_infrastructure.py
    python scripts/audit_digital_infrastructure.py --corpus europeana ina bfi
    python scripts/audit_digital_infrastructure.py --limit 5 --timeout 30
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.digital_infrastructure_audit import audit_url

OUTPUT_DIR = BASE_DIR / "data" / "output"
CSV_FILENAME = "digital_infrastructure_audit.csv"
JSON_FILENAME = "digital_infrastructure_audit.json"


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


def main() -> int:
    args = parse_args()
    corpora = select_corpora(args)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []
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
                "category_code": corpus.get("category_code", ""),
                "entity_level": corpus.get("entity_level", ""),
                "coverage_level": corpus.get("coverage_level", ""),
                "collection_completeness": corpus.get("collection_completeness", ""),
            }
        )
        records.append(record)

    dataframe = pd.DataFrame(records)
    csv_path = OUTPUT_DIR / CSV_FILENAME
    json_path = OUTPUT_DIR / JSON_FILENAME
    dataframe.to_csv(csv_path, index=False, encoding="utf-8-sig")
    json_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")

    reachable = int(dataframe["reachable"].sum()) if not dataframe.empty else 0
    print(f"Auditoria concluída: {len(dataframe)} unidades; {reachable} superfícies alcançáveis.")
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
