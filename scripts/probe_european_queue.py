#!/usr/bin/env python3
"""Sonda candidatos individuais da fila europeia sem incorporá-los ao corpus."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.digital_infrastructure.european_queue import (
    is_source_only,
    load_european_queue,
)
from memoria_audiovisual.digital_infrastructure.queue_probe import probe_queue_candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--queue",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_fila_pesquisa_europa.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=BASE_DIR / "data/output/observatorio_sondagem_tecnica_fila_europa.json",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = [row for row in load_european_queue(args.queue) if not is_source_only(row)]
    if args.limit is not None:
        rows = rows[: args.limit]

    existing: dict[str, dict[str, object]] = {}
    if args.resume and args.output.exists():
        payload = json.loads(args.output.read_text(encoding="utf-8"))
        existing = {
            str(item["unit_code"]): dict(item)
            for item in payload.get("items", [])
            if isinstance(item, dict) and item.get("unit_code")
        }

    results = dict(existing)
    for position, row in enumerate(rows, start=1):
        code = str(row.get("unit_code") or "")
        if args.resume and code in results:
            print(f"[{position}/{len(rows)}] {code}: já sondado")
            continue
        print(f"[{position}/{len(rows)}] {code}: {row.get('source_url', '')}")
        try:
            results[code] = probe_queue_candidate(row, timeout=args.timeout).to_dict()
        except Exception as exc:  # mantém a fila reiniciável sem promover falhas
            results[code] = {
                "unit_code": code,
                "source_url": str(row.get("source_url") or ""),
                "reachable": False,
                "observable_surface_confirmed": False,
                "institutional_identity_confirmed": None,
                "audiovisual_relevance_confirmed": None,
                "evidence_ids": [],
                "technical_signals": [],
                "error": f"{type(exc).__name__}: {exc}",
            }

    payload = {
        "queue_path": str(args.queue),
        "promotion_performed": False,
        "corpora_modified": False,
        "item_count": len(results),
        "items": [results[key] for key in sorted(results)],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "output": str(args.output),
        "item_count": len(results),
        "promotion_performed": False,
        "corpora_modified": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
