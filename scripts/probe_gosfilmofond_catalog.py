"""Run the non-invasive Gosfilmofond catalogue probe and persist JSON evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from memoria_audiovisual.config import OUTPUT_DIR
from memoria_audiovisual.gosfilmofond_probe import run_gosfilmofond_probe

OUTPUT_FILENAME = "gosfilmofond_catalog_probe.json"


def main() -> int:
    payload = run_gosfilmofond_probe()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / OUTPUT_FILENAME
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Gosfilmofond public catalogue probe")
    print(f"- gate: {payload['gate_assessment']}")
    print(f"- robots mode: {payload['robots'].get('mode')}")
    print(
        "- robots status: "
        f"{payload['robots'].get('status_code')} "
        f"error={payload['robots'].get('error')}"
    )
    for target in payload["robots"].get("targets", []):
        print(
            "- robots target: "
            f"allowed={target.get('allowed')} "
            f"reason={target.get('reason')} "
            f"url={target.get('url')}"
        )
    excerpt = payload["robots"].get("robots_excerpt", "")
    if excerpt:
        print(f"- robots excerpt: {excerpt}")
    catalog = payload.get("catalog") or {}
    print(f"- catalog status: {catalog.get('status_code')}")
    print(f"- film links in initial HTML: {catalog.get('film_links_count', 0)}")
    print(
        "- enumeration mechanisms: "
        + ", ".join(payload.get("enumeration_mechanisms", []))
    )
    for item in payload.get("sitemaps", []):
        parsed = item.get("parsed") or {}
        print(
            f"- sitemap {item['url']}: status={item.get('status_code')} "
            f"urls={parsed.get('url_count', 0)} films={parsed.get('film_url_count', 0)}"
        )
    rest = payload.get("rest") or {}
    if rest:
        print(
            f"- REST: status={rest.get('status_code')} "
            f"routes={rest.get('routes_count', 0)} "
            f"candidate_routes={len(rest.get('candidate_routes', []))}"
        )
    print(f"- evidence: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
