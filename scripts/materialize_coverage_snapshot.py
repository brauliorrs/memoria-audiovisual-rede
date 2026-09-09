"""Materializa o Coverage Snapshot v1.0 a partir da matriz real de cobertura."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.scientific_infrastructure.coverage_snapshot import (
    build_coverage_snapshot,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--source-snapshot-id", required=True)
    parser.add_argument("--started-at", required=True)
    parser.add_argument("--finished-at", required=True)
    parser.add_argument("--duration-seconds", type=float, required=True)
    parser.add_argument("--pipeline-commit", required=True)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=BASE_DIR / "data/reference_corpus/manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BASE_DIR
        / "data/reference_corpus/snapshots/coverage_snapshot_v1.0.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = json.loads(args.coverage.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    payload = build_coverage_snapshot(
        coverage_rows=rows,
        source_snapshot_id=args.source_snapshot_id,
        started_at=args.started_at,
        finished_at=args.finished_at,
        duration_seconds=args.duration_seconds,
        pipeline_commit=args.pipeline_commit,
        manifest=manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary = payload["summary"]
    print("Coverage Snapshot v1.0 materializado.")
    print(f"- corpora: {summary['corpus_count']}")
    print(f"- grupos detectores: {summary['detector_group_count']}")
    print(f"- estados de cobertura: {summary['parameter_count']}")
    print(f"- arquivo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
