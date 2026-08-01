#!/usr/bin/env python3
"""Valida semanticamente uma rodada antes da consolidação histórica."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.digital_infrastructure.postflight import (
    validate_periodic_run,
    write_postflight_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Valida a coerência semântica da rodada infraestrutura digital.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--state-dir", type=Path, default=BASE_DIR / "data" / "digital_infrastructure")
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report = validate_periodic_run(snapshot_id=args.snapshot_id, state_dir=args.state_dir)
    write_postflight_report(report, args.report)
    print(
        f"Pós-flight {args.snapshot_id}: ok={report.ok}; "
        f"corpora={report.corpus_count}; cobertura={report.coverage_row_count}; "
        f"observações={report.observation_count}; issues={len(report.issues)}"
    )
    for issue in report.issues:
        print(f"[{issue.severity}] {issue.code}: {issue.message}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
