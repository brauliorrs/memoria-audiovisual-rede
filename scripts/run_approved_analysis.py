"""Run only analysis instruments admitted for MAR production.

This executor is intentionally separate from corpus ingestion. Experimental
instruments are rejected by the registry even when explicitly requested.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.analysis_instruments import (
    InstrumentRegistryError,
    load_instrument_registry,
    run_production_analysis,
)
from memoria_audiovisual.config import OUTPUT_DIR


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa somente instrumentos de análise admitidos em produção."
    )
    parser.add_argument(
        "--instrument",
        action="append",
        default=[],
        help="ID de instrumento de produção. Pode ser repetido. Sem opção, usa o ciclo padrão.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Lista instrumentos e estados sem executar análises.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    registry = load_instrument_registry()
    if args.list:
        payload = [
            {
                "id": spec.instrument_id,
                "label": spec.label,
                "lifecycle": spec.lifecycle,
                "version": spec.version,
                "default_cycle": spec.default_cycle,
                "validation_status": spec.validation_status,
            }
            for spec in registry.values()
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    requested = args.instrument or None
    try:
        manifest = run_production_analysis(
            output_dir=OUTPUT_DIR,
            requested=requested,
            source_cycle_status="successful_full_refresh",
        )
    except InstrumentRegistryError as exc:
        print(f"Análise de produção bloqueada: {exc}", file=sys.stderr)
        return 2

    print("Instrumentos de análise de produção concluídos.")
    for row in manifest["instruments"]:
        print(f"- {row['instrument_id']} {row['version']}: {row['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
