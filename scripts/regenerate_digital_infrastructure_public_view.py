from __future__ import annotations

import argparse
import json
from pathlib import Path

from memoria_audiovisual.digital_infrastructure.event_review import LongitudinalEventReviewService
from memoria_audiovisual.digital_infrastructure.ledger import AtomicLedger
from memoria_audiovisual.digital_infrastructure.publication_revision import (
    PublicationRevisionStore,
    regenerate_publication,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cria nova revisão derivada da visão pública sem sobrescrever versões anteriores."
    )
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--requested-by", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        events = payload.get("events", [])
    else:
        events = payload
    if not isinstance(events, list):
        raise ValueError("o arquivo de eventos deve conter uma lista ou um objeto com a chave events")

    service = LongitudinalEventReviewService(AtomicLedger(args.ledger))
    store = PublicationRevisionStore(args.output_root)
    manifest = regenerate_publication(
        snapshot_id=args.snapshot_id,
        events=events,
        review_service=service,
        store=store,
        reason=args.reason,
        requested_by=args.requested_by,
    )
    print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
