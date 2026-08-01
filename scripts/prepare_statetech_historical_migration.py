"""Analisa CSV/JSON históricos sem gravar no ledger.

Exemplo:
    python scripts/prepare_statetech_historical_migration.py \
      --input data/output/digital_infrastructure_audit.json \
      --report data/migration/historical_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.statetech.historical_migration import HistoricalMigrationAnalyzer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepara migração histórica exclusivamente em dry-run.")
    parser.add_argument("--input", required=True, help="Arquivo histórico .csv ou .json.")
    parser.add_argument("--report", required=True, help="Relatório de compatibilidade em JSON.")
    parser.add_argument(
        "--fail-on-blocked",
        action="store_true",
        help="Retorna código 2 quando houver registros bloqueados.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = HistoricalMigrationAnalyzer().analyze(args.input)
    destination = Path(args.report)
    if destination.suffix.casefold() != ".json":
        raise SystemExit("o relatório deve usar extensão .json")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        "Dry-run concluído: "
        f"{report.total_rows} registros; "
        f"{report.compatible_rows} compatíveis; "
        f"{report.review_required_rows} exigem revisão; "
        f"{report.blocked_rows} bloqueados."
    )
    print(f"Relatório: {destination}")
    if args.fail_on_blocked and report.blocked_rows:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
