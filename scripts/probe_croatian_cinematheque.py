"""Run the Croatian Cinematheque/HDA discovery probe and persist evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.croatian_cinematheque_probe import (
    run_croatian_cinematheque_probe,
)

OUTPUT_FILENAME = "croatian_cinematheque_probe.json"


def main() -> int:
    payload = run_croatian_cinematheque_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / OUTPUT_FILENAME
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Croatian Cinematheque / HDA public-surface probe")
    print(f"- gate: {payload['gate_assessment']}")
    print(
        "- mechanisms: "
        + ", ".join(payload.get("enumeration_mechanisms", []))
    )
    for name, robots in payload.get("robots", {}).items():
        print(
            f"- robots {name}: mode={robots.get('mode')} "
            f"status={robots.get('status_code')} error={robots.get('error')}"
        )
    for surface in payload.get("surfaces", []):
        parsed = surface.get("parsed") or {}
        print(
            f"- surface {surface.get('kind')}: status={surface.get('status_code')} "
            f"forms={len(parsed.get('forms', []))} "
            f"discovery_links={len(parsed.get('discovery_links', []))}"
        )
    print(f"- evidence: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
