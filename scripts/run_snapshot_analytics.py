#!/usr/bin/env python3
"""Executa e persiste os indicadores nativos de um snapshot consolidado."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.analytics.pipeline import analyze_snapshot


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--methodology-version", default="1.0.0")
    parser.add_argument(
        "--run-output",
        type=Path,
        help="Cópia opcional da execução antes da persistência.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = analyze_snapshot(
        snapshot_id=args.snapshot_id,
        coverage_path=args.coverage,
        methodology_version=args.methodology_version,
        output_root=args.output_root,
        metadata={"coverage_path": str(args.coverage)},
    )
    payload = result.run.to_dict()
    if args.run_output is not None:
        args.run_output.parent.mkdir(parents=True, exist_ok=True)
        args.run_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({
        "snapshot_id": result.run.snapshot_id,
        "methodology_version": result.run.methodology_version,
        "indicator_count": result.run.indicator_count,
        "status": result.run.status,
        "manifest": result.manifest.to_dict() if result.manifest else None,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
