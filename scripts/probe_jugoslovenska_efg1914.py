"""Run the EFG1914 provenance/access gate for Jugoslovenska Kinoteka."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.jugoslovenska_efg1914_probe import (
    dumps,
    run_efg1914_probe,
)

OUTPUT_PATH = OUTPUT_DIR / "jugoslovenska_efg1914_probe.json"


def main() -> int:
    result = run_efg1914_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps(result), encoding="utf-8")
    print(f"EFG1914 Jugoslovenska provider gate: {result['gate_assessment']}")
    print(f"Facet count (unverified): {result['provider_facet_count']}")
    print(f"Records enumerated: {result['records_enumerated']}")
    print(f"Evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
