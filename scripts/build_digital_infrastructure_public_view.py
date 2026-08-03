#!/usr/bin/env python3
"""Gera a visão pública derivada sem realizar publicação externa."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.event_review import LongitudinalEventReviewService
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.public_view import PublicViewStore, build_public_view


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=Path("data/digital_infrastructure/ledger.jsonl"))
    parser.add_argument("--output-root", type=Path, default=Path("data/digital_infrastructure/public"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("o relatório de triagem deve conter uma lista")
    service = LongitudinalEventReviewService(AtomicLedger(args.ledger))
    events = build_public_view((dict(item) for item in payload), service)
    manifest = PublicViewStore(args.output_root).write(args.snapshot_id, events)
    print(json.dumps(manifest.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
