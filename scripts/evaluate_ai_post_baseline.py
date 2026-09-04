#!/usr/bin/env python3
"""Valida a fila humana e materializa métricas experimentais do T2A."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.ai_post_baseline_validation import (
    evaluate_human_reviews,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--amendments", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Falha quando ainda existem unidades sem revisão humana concluída.",
    )
    return parser.parse_args()


def _read_jsonl(path: Path | None) -> list[dict]:
    if path is None or not path.exists():
        return []
    rows: list[dict] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise SystemExit(f"emenda inválida na linha {line_number}")
        rows.append(value)
    return rows


def main() -> int:
    args = parse_args()
    payload = json.loads(args.queue.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise SystemExit("fila de revisão sem entries válidas")
    amendments = _read_jsonl(args.amendments)
    report = evaluate_human_reviews(entries, amendments=amendments)
    report["queue_id"] = payload.get("queue_id")
    report["source_run_id"] = payload.get("source_run_id")
    report["amendments_source"] = str(args.amendments) if args.amendments else None
    report["status"] = (
        "completed_pending_activation_decision"
        if report["pending_units"] == 0
        else "pending_human_review"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if args.require_complete and report["pending_units"]:
        raise SystemExit(
            f"revisão humana incompleta: {report['pending_units']} unidade(s) pendente(s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
