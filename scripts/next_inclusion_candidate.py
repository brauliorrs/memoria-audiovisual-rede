"""Show the next MAR corpus candidates from the versioned inclusion queue."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.inclusion_queue import (
    InclusionQueueError,
    write_next_inclusion_candidates,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materializa os próximos candidatos da fila de inclusão, sem incorporá-los automaticamente."
    )
    parser.add_argument("--limit", type=int, default=3, help="Quantidade de candidatos a listar.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        payload = write_next_inclusion_candidates(
            output_dir=OUTPUT_DIR,
            limit=args.limit,
        )
    except InclusionQueueError as exc:
        print(f"Fila de inclusão inválida: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
