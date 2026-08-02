#!/usr/bin/env python3
"""Gera relatório derivado de sensibilidade do índice de interoperabilidade."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.pipeline import load_coverage_rows
from memoria_audiovisual.analytics.sensitivity import analyze_interoperability_sensitivity


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = load_coverage_rows(args.coverage, snapshot_id=args.snapshot_id)
    report = analyze_interoperability_sensitivity(
        IndicatorContext(snapshot_id=args.snapshot_id, coverage_rows=rows)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise FileExistsError(f"relatório de sensibilidade já existe: {args.output}")
    args.output.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
