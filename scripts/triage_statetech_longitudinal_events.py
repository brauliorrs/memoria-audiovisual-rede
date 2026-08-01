from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.statetech.event_triage import triage_events


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Classifica eventos longitudinais antes da publicação.")
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--coverage-dir", type=Path, default=BASE_DIR / "data/statetech/coverage")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def _load_events(snapshot_id: str, coverage_dir: Path) -> list[dict]:
    snapshot_dir = coverage_dir / snapshot_id
    changes_path = snapshot_dir / "parameter_changes.json"
    if changes_path.exists():
        payload = json.loads(changes_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("parameter_changes.json deve conter uma lista")
        return [dict(item) for item in payload]

    coverage_path = snapshot_dir / "parameter_coverage.json"
    payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("parameter_coverage.json deve conter uma lista")
    return [
        {
            "corpus_code": item["corpus_code"],
            "detector_group": item["detector_group"],
            "current_snapshot_id": snapshot_id,
            "change_type": "baseline_created" if item.get("status") != "missing_observation" else "still_missing",
            "previous_values": [],
            "current_values": item.get("detected_values", []),
        }
        for item in payload
    ]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    source = _load_events(args.snapshot_id, args.coverage_dir)
    events = triage_events(source)
    counts = Counter(item.triage_class for item in events)
    payload = {
        "snapshot_id": args.snapshot_id,
        "event_count": len(events),
        "review_required_count": sum(item.review_required for item in events),
        "publishable_count": sum(item.publication_status == "publishable" for item in events),
        "counts_by_class": dict(sorted(counts.items())),
        "events": [item.to_dict() for item in events],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Triagem concluída: {len(events)} eventos; {payload['review_required_count']} exigem revisão.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
