#!/usr/bin/env python3
"""Materializa os nove resultados científicos a partir do Coverage Snapshot v1.0."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from memoria_audiovisual.scientific_infrastructure.indicator_results_registry import (
    write_indicator_results_registry,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--created-at", default=None)
    parser.add_argument("--pipeline-commit", default=os.getenv("GITHUB_SHA"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = write_indicator_results_registry(
        args.repository_root,
        output_path=args.output,
        created_at=args.created_at,
        pipeline_commit=args.pipeline_commit,
    )
    print(f"Registro científico de resultados materializado: {path}")
    print("- indicadores: 9")
    print("- status: completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
