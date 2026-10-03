"""Run the fail-closed Image'Est public catalogue probe."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.image_est_probe import dumps_probe, run_image_est_probe

OUTPUT_PATH = OUTPUT_DIR / "image_est_probe.json"


def main() -> int:
    payload = run_image_est_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(dumps_probe(payload), encoding="utf-8")
    print(dumps_probe(payload), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
