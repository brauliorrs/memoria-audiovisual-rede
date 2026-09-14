#!/usr/bin/env python3
"""Executa, persiste e avalia a sensibilidade analítica de um snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.analytics.base import IndicatorContext
from memoria_audiovisual.analytics.catalog import IndicatorCatalog
from memoria_audiovisual.analytics.pipeline import (
    analyze_snapshot,
    default_indicator_registry,
    load_coverage_rows,
)
from memoria_audiovisual.analytics.sensitivity import analyze_interoperability_sensitivity


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--coverage", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--methodology-version", default="1.0.0")
    parser.add_argument(
        "--registry",
        "--catalog",
        dest="registry",
        type=Path,
        default=Path("data/templates/analytics/indicator_registry.json"),
        help="Registro científico canônico dos indicadores.",
    )
    parser.add_argument(
        "--run-output",
        type=Path,
        help="Cópia opcional da execução antes da persistência.",
    )
    parser.add_argument(
        "--sensitivity-output",
        type=Path,
        help="Destino opcional; por padrão usa o diretório analítico do snapshot.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = default_indicator_registry()
    catalog = IndicatorCatalog.load(args.registry)
    catalog.validate_registry(registry)

    result = analyze_snapshot(
        snapshot_id=args.snapshot_id,
        coverage_path=args.coverage,
        methodology_version=args.methodology_version,
        registry=registry,
        output_root=args.output_root,
        metadata={
            "coverage_path": str(args.coverage),
            "indicator_registry_path": str(args.registry),
            "indicator_registry_version": catalog.catalog_version,
        },
    )
    payload = result.run.to_dict()
    if args.run_output is not None:
        args.run_output.parent.mkdir(parents=True, exist_ok=True)
        args.run_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    coverage_rows = load_coverage_rows(args.coverage, snapshot_id=args.snapshot_id)
    sensitivity = analyze_interoperability_sensitivity(
        IndicatorContext(
            snapshot_id=args.snapshot_id,
            coverage_rows=coverage_rows,
            methodology_version=args.methodology_version,
        )
    )
    sensitivity_output = args.sensitivity_output or (
        args.output_root / args.snapshot_id / "interoperability_sensitivity.json"
    )
    sensitivity_output.parent.mkdir(parents=True, exist_ok=True)
    if sensitivity_output.exists():
        raise FileExistsError(
            f"relatório de sensibilidade já existe: {sensitivity_output}"
        )
    sensitivity_output.write_text(
        json.dumps(sensitivity.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "snapshot_id": result.run.snapshot_id,
        "methodology_version": result.run.methodology_version,
        "indicator_registry_version": catalog.catalog_version,
        "indicator_count": result.run.indicator_count,
        "status": result.run.status,
        "manifest": result.manifest.to_dict() if result.manifest else None,
        "sensitivity_output": str(sensitivity_output),
        "sensitivity_interpretation": sensitivity.interpretation,
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
