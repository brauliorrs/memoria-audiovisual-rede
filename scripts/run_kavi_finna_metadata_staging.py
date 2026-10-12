"""Explicitly bounded, audited KAVI/Finna metadata staging; no promotion."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from memoria_audiovisual.config import HEADERS
from memoria_audiovisual.kavi_elonet_probe import USER_AGENT
from memoria_audiovisual.kavi_finna_adapter import FinnaMetadataSource, FinnaScope
from memoria_audiovisual.metadata_staging import StageRejected
from scripts.kavi_finna_batch_gate import execute_verified_batch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="KAVI metadata-only staging with offline audit, NOT media or promotion"
    )
    parser.add_argument(
        "--evidence-sha256", required=True,
        help="SHA256 of independently verified public scope-discovery evidence",
    )
    parser.add_argument(
        "--directory", type=Path, default=ROOT / "data" / "staging" / "kavi-finna",
        help="Local directory; intentionally excluded from git",
    )
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument(
        "--expected-total", type=int,
        help="Required when resuming; previously independently recorded preflight count",
    )
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--expiry-margin-seconds", type=float, default=30.0)
    parser.add_argument(
        "--execute", action="store_true",
        help="Required for public API requests and local checkpoint writes",
    )
    args = parser.parse_args(argv)
    if not 1 <= args.max_pages <= 25:
        parser.error("--max-pages must be between 1 and 25")
    if not 0.5 <= args.delay_seconds <= 30.0:
        parser.error("--delay-seconds must be between 0.5 and 30")
    if not 0 <= args.expiry_margin_seconds <= 3600:
        parser.error("--expiry-margin-seconds must be between 0 and 3600")
    if args.resume and args.expected_total is None:
        parser.error("--resume requires independently recorded --expected-total")
    if args.expected_total is not None and args.expected_total < 0:
        parser.error("--expected-total must be nonnegative")
    scope = FinnaScope(
        building_code="0/KAVI/", format_code="0/Video/",
        evidence_sha256=args.evidence_sha256,
    )
    if not args.execute:
        print("DRY RUN: no Finna API requests or local artifacts.")
        print("Neither media download nor corpus promotion is supported.")
        return 0
    with requests.Session() as session:
        session.headers.update({
            **HEADERS, "User-Agent": f"{USER_AGENT}/1.0 (+metadata-only-staging)",
            "Accept": "application/json",
        })
        try:
            result = execute_verified_batch(
                FinnaMetadataSource(session, scope),
                args.directory,
                max_pages=args.max_pages,
                resume=args.resume,
                expected_total=args.expected_total,
                delay_seconds=args.delay_seconds,
                expiry_margin_seconds=args.expiry_margin_seconds,
            )
        except (StageRejected, ValueError) as exc:
            # All rejection messages are stable codes, never raw cursors/URLs.
            print(json.dumps({
                "audit_status": "rejected",
                "reason": str(exc),
                "promotion_authorized": False,
                "media_downloaded": False,
            }, ensure_ascii=False, sort_keys=True))
            return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
