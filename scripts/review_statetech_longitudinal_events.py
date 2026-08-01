#!/usr/bin/env python3
"""Exporta fila e importa decisões sobre eventos longitudinais."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from memoria_audiovisual.statetech.event_review import (
    LongitudinalEventReview,
    LongitudinalEventReviewService,
)
from memoria_audiovisual.statetech.ledger import AtomicLedger


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("o JSON deve conter uma lista")
        return [dict(item) for item in payload]
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(item) for item in csv.DictReader(handle)]
    raise ValueError("arquivo deve ser .json ou .csv")


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.casefold() == ".json":
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return
    if path.suffix.casefold() != ".csv":
        raise ValueError("saída deve ser .json ou .csv")
    fields = list(rows[0].keys()) if rows else [
        "event_id", "snapshot_id", "corpus_code", "detector_group", "change_type",
        "triage_class", "severity", "current_status", "confirmation_count",
        "required_confirmations", "publication_status",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _evidence_ids(value: Any) -> tuple[str, ...]:
    if isinstance(value, list):
        return tuple(str(item).strip() for item in value if str(item).strip())
    text = str(value or "")
    return tuple(item.strip() for item in text.replace(";", "|").split("|") if item.strip())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("export", "import"))
    parser.add_argument("--events", type=Path)
    parser.add_argument("--input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ledger", type=Path, default=Path("data/statetech/ledger.jsonl"))
    parser.add_argument("--include-resolved", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    service = LongitudinalEventReviewService(AtomicLedger(args.ledger))
    if args.operation == "export":
        if args.events is None or args.output is None:
            raise SystemExit("export exige --events e --output")
        events = _load_rows(args.events)
        rows = [dict(item) for item in service.export_queue(events, include_resolved=args.include_resolved)]
        _write_rows(args.output, rows)
        print(json.dumps({"exported": len(rows), "output": str(args.output)}, ensure_ascii=False))
        return 0

    if args.input is None:
        raise SystemExit("import exige --input")
    reviews: list[LongitudinalEventReview] = []
    for position, row in enumerate(_load_rows(args.input), start=1):
        required = ("event_id", "reviewer_id", "reviewer_role", "decision", "justification")
        missing = [name for name in required if not str(row.get(name) or "").strip()]
        if missing:
            raise ValueError(f"linha {position}: campos ausentes: {', '.join(missing)}")
        kwargs: dict[str, Any] = {
            "event_id": str(row["event_id"]).strip(),
            "reviewer_id": str(row["reviewer_id"]).strip(),
            "reviewer_role": str(row["reviewer_role"]).strip(),
            "decision": str(row["decision"]).strip(),
            "justification": str(row["justification"]).strip(),
            "evidence_ids": _evidence_ids(row.get("evidence_ids")),
            "reclassified_as": str(row.get("reclassified_as") or "").strip() or None,
            "conflict_of_interest_status": str(row.get("conflict_of_interest_status") or "none_declared").strip(),
            "supersedes_review_id": str(row.get("supersedes_review_id") or "").strip() or None,
        }
        reviewed_at = str(row.get("reviewed_at") or "").strip()
        if reviewed_at:
            kwargs["reviewed_at"] = reviewed_at
        review = LongitudinalEventReview(**kwargs)
        service.register(review)
        reviews.append(review)
    print(json.dumps({"imported": len(reviews)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
