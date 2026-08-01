#!/usr/bin/env python3
"""Valida o ciclo periódico antes de qualquer requisição de rede."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.statetech.preflight import PeriodicReviewPreflight


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida a revisão periódica Estado–tecnologia sem coletar dados.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--state-dir", type=Path, default=BASE_DIR / "data" / "statetech")
    parser.add_argument("--corpus", nargs="*", default=[])
    parser.add_argument("--history-exists", action="store_true")
    parser.add_argument("--report", type=Path, default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = PeriodicReviewPreflight(BASE_DIR, args.state_dir).validate(
        snapshot_id=args.snapshot_id,
        corpora=CORPORA,
        selected_corpora=args.corpus,
        history_exists=args.history_exists,
    )
    payload = report.to_dict()
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text)
    return 0 if report.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
