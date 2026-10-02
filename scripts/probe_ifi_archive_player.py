"""Run the non-invasive IFI Archive Player discovery probe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.ifi_archive_player_probe import (
    run_ifi_archive_player_probe,
)

OUTPUT_FILENAME = "ifi_archive_player_probe.json"


def main() -> int:
    payload = run_ifi_archive_player_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / OUTPUT_FILENAME
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("IFI Archive Player public-surface probe")
    print(f"- gate: {payload['gate_assessment']}")
    print(f"- robots mode: {payload['robots'].get('mode')}")
    print(
        "- mechanisms: "
        + ", ".join(payload.get("enumeration_mechanisms", []))
    )
    for surface in payload.get("surfaces", []):
        parsed = surface.get("parsed") or {}
        print(
            f"- surface {surface.get('kind')}: "
            f"status={surface.get('status_code')} "
            f"film_candidates={parsed.get('film_links_count', 0)} "
            f"search_forms={len(parsed.get('search_forms', []))} "
            f"pagination={len(parsed.get('pagination_links', []))}"
        )
    bounded = payload.get("bounded_post_sitemap_probe") or {}
    if bounded:
        print(
            "- bounded post-sitemap probe: "
            f"reproducible={bounded.get('reproducible_bounded_enumeration')} "
            f"partitions={bounded.get('partitions_selected', [])} "
            f"unique={bounded.get('unique_film_permalink_candidates', 0)} "
            f"all_shards={bounded.get('all_discovered_post_sitemaps_covered')}"
        )
    rest = payload.get("rest") or {}
    if rest:
        print(
            f"- REST: status={rest.get('status_code')} "
            f"routes={rest.get('routes_count', 0)} "
            f"candidates={len(rest.get('candidate_routes', []))}"
        )
    print(f"- evidence: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
