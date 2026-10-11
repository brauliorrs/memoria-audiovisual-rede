"""Run the KAVI/Elonet/Finna public API surface probe (#82)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.kavi_elonet_probe import dumps, run_probe

OUTPUT = OUTPUT_DIR / "kavi_elonet_probe.json"


def main() -> int:
    report = run_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(dumps(report), encoding="utf-8")
    print(f"KAVI Elonet #82 gate: {report['gate_assessment']}")
    for probe in report["api_probes"]:
        print(f"{probe['probe']}: HTTP {probe['status']} error={probe['error']}")
    print(f"Staged authorized: {report['staged_collector_authorized']}")
    print(f"Evidence: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
