"""Run the Mémoire Filmique subordinate probe for Jean Vigo #80."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.memoire_filmique_probe import (
    dumps_probe,
    run_memoire_filmique_probe,
)

OUTPUT_PATH = OUTPUT_DIR / "memoire_filmique_probe.json"


def main() -> int:
    payload = run_memoire_filmique_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps_probe(payload), encoding="utf-8")
    print("Mémoire Filmique subordinate probe — Jean Vigo #80")
    print(f"- gate: {payload['gate_assessment']}")
    enumeration = payload.get("enumeration", {})
    print(
        "- enumeration: "
        f"{enumeration.get('unique_item_count', 0)} / "
        f"{enumeration.get('reported_result_count')}"
    )
    print(
        "- semantic sample: "
        f"{payload.get('semantic_confirmed_count', 0)} / "
        f"{payload.get('semantic_sample_size', 0)}"
    )
    print(
        "- providers parsed: "
        f"{payload.get('provider_present_count', 0)} / "
        f"{payload.get('semantic_sample_size', 0)}"
    )
    print(f"- evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
