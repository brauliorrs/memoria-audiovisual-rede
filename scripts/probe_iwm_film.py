"""Run the fail-closed Imperial War Museums Film Archive probe."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.iwm_film_probe import dumps_probe, run_iwm_film_probe

OUTPUT_PATH = OUTPUT_DIR / "iwm_film_probe.json"


def main() -> int:
    payload = run_iwm_film_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps_probe(payload), encoding="utf-8")
    print("Imperial War Museums Film Archive public-surface probe")
    print(f"- gate: {payload['gate_assessment']}")
    print(
        "- mechanisms: "
        + ", ".join(payload.get("enumeration_mechanisms", []))
    )
    summary = payload.get("discovery_summary") or {}
    print(
        "- records discovered: "
        f"{summary.get('record_permalinks_discovered', 0)}"
    )
    print(f"- evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
