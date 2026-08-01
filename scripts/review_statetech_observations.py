"""Exporta filas e importa decisões curatoriais em CSV ou JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.statetech.curatorial_review import CuratorialReviewService
from memoria_audiovisual.statetech.ledger import AtomicLedger
from memoria_audiovisual.statetech.review_files import export_review_queue, import_review_decisions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Opera a fila de revisão curatorial Estado–tecnologia.")
    parser.add_argument("command", choices=("export", "import"))
    parser.add_argument("--ledger", type=Path, default=BASE_DIR / "data/statetech/ledger.jsonl")
    parser.add_argument("--observations", type=Path, help="JSON com observações para exportação")
    parser.add_argument("--input", type=Path, help="CSV ou JSON de decisões para importação")
    parser.add_argument("--output", type=Path, help="Destino CSV ou JSON da fila")
    parser.add_argument("--include-reviewed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service = CuratorialReviewService(AtomicLedger(args.ledger))
    if args.command == "export":
        if args.observations is None or args.output is None:
            raise SystemExit("export exige --observations e --output")
        payload = json.loads(args.observations.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise SystemExit("--observations deve conter uma lista JSON")
        path = export_review_queue(
            service, payload, args.output, include_reviewed=args.include_reviewed
        )
        print(f"Fila exportada: {path}")
        return 0
    if args.input is None:
        raise SystemExit("import exige --input")
    reviews = import_review_decisions(service, args.input)
    print(f"Decisões importadas: {len(reviews)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
