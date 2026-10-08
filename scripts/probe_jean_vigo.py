"""Run the fail-closed Jean Vigo Institute public-surface probe."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.jean_vigo_probe import dumps_probe, run_jean_vigo_probe

OUTPUT_PATH = OUTPUT_DIR / "jean_vigo_probe.json"


def main() -> int:
    payload = run_jean_vigo_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps_probe(payload), encoding="utf-8")
    print("Jean Vigo Institute public-surface probe")
    print(f"- gate: {payload['gate_assessment']}")
    print(f"- sitemap pages: {payload.get('sitemap_pages_total', 0)}")
    print(
        "- external archive hints: "
        f"{len(payload.get('external_archive_hints', []))}"
    )
    print(f"- evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
