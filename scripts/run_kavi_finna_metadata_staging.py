"""Explicitly bounded, metadata-only KAVI/Finna staging (never corpus promotion)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memoria_audiovisual.config import HEADERS
from memoria_audiovisual.kavi_elonet_probe import USER_AGENT
from memoria_audiovisual.kavi_finna_adapter import FinnaMetadataSource, FinnaScope
from memoria_audiovisual.metadata_staging import (
    public_stage_summary,
    stage_metadata,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="KAVI metadata-only staging, NOT media download or promotion",
    )
    parser.add_argument(
        "--evidence-sha256", required=True,
        help="SHA256 of previously validated scope-discovery evidence",
    )
    parser.add_argument(
        "--directory", type=Path, default=ROOT / "data" / "staging" / "kavi-finna",
        help="Local directory; intentionally excluded from git",
    )
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument(
        "--execute", action="store_true",
        help="Required to enable network requests and local artifact writes",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max_pages <= 25:
        parser.error("--max-pages must be between 1 and 25")
    if not 0.5 <= args.delay_seconds <= 30.0:
        parser.error("--delay-seconds must be between 0.5 and 30")
    scope = FinnaScope(
        building_code="0/KAVI/", format_code="0/Video/",
        evidence_sha256=args.evidence_sha256,
    )
    if not args.execute:
        print("DRY RUN: staged metadata only; use --execute to call public Finna API.")
        print("No media will be downloaded and no active corpus will be modified.")
        return 0
    session = requests.Session()
    session.headers.update({
        **HEADERS, "User-Agent": f"{USER_AGENT}/1.0 (+metadata-only-staging)",
        "Accept": "application/json",
    })
    try:
        result = stage_metadata(
            FinnaMetadataSource(session, scope),
            args.directory,
            max_pages=args.max_pages,
            resume=args.resume,
            request_delay_seconds=args.delay_seconds,
        )
    finally:
        session.close()
    # Never print or upload raw resumption tokens.
    print(json.dumps(public_stage_summary(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
