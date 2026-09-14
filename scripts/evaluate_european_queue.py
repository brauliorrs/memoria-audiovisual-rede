#!/usr/bin/env python3
"""Avalia a fila europeia sem promover candidatos para CORPORA."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.digital_infrastructure.european_queue import (
    evaluate_queue_rows,
    load_european_queue,
    write_evaluations,
)
from memoria_audiovisual.digital_infrastructure.queue_probe import (
    apply_probe_to_row,
    load_probe_results,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_fila_pesquisa_europa.csv",
    )
    parser.add_argument(
        "--probe-results",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_sondagem_tecnica_fila_europa.json",
        help="Resultados verificáveis da sondagem técnica; ausente mantém critérios indeterminados.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_elegibilidade_fila_europa.json",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_elegibilidade_fila_europa.csv",
    )
    parser.add_argument("--minimum-evidence-count", type=int, default=2)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load_european_queue(args.queue)
    probes = load_probe_results(args.probe_results)
    enriched_rows = tuple(
        apply_probe_to_row(row, probes.get(str(row.get("unit_code") or "")))
        for row in rows
    )
    evaluations = evaluate_queue_rows(
        enriched_rows, minimum_evidence_count=args.minimum_evidence_count
    )
    write_evaluations(
        evaluations,
        json_path=args.json_output,
        csv_path=args.csv_output,
    )

    counts = Counter(item.evaluation_status for item in evaluations)
    summary = {
        "queue_path": str(args.queue),
        "probe_results_path": str(args.probe_results),
        "technical_probe_count": len(probes),
        "evaluated_count": len(evaluations),
        "status_counts": dict(sorted(counts.items())),
        "promotion_performed": False,
        "corpora_modified": False,
        "curatorial_decision_automated": False,
        "json_output": str(args.json_output),
        "csv_output": str(args.csv_output),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
