"""Run Jugoslovenska Kinoteka #81 public discovery without admitting a corpus."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.jugoslovenska_kinoteka_probe import dumps, run_probe

OUTPUT_PATH = OUTPUT_DIR / "jugoslovenska_kinoteka_probe.json"


def main() -> int:
    result = run_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps(result), encoding="utf-8")
    print(f"Jugoslovenska Kinoteka #81: {result['gate_assessment']}")
    print(f"URLs enumerated: {result['enumerated_public_url_count']}")
    print(f"Traversal complete: {result['traversal_complete']}")
    print(f"Staged collector authorized: {result['staged_collector_authorized']}")
    print(f"Evidence: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
