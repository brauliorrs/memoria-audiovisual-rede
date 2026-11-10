"""Opt-in single-page parser smoke test after validated source availability.

No detail-page fetch, no media retrieval, no pagination, no writes.
A nonempty parsed page is not proof of full corpus completeness or playback.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
from urllib.error import HTTPError, URLError
from urllib.request import Request, HTTPSHandler, build_opener

from memoria_audiovisual.czech_television import parse_czech_television_catalog_page
from memoria_audiovisual.eye import (
    extract_eye_declared_fragment_total,
    parse_eye_fragment_list_page,
)
from scripts.probe_monthly_sources import (
    NoRedirect, SOURCES, USER_AGENT, robots_preflight, classify_http,
)

SOURCE_CODES = frozenset({"eye", "czech_tv"})
MAX_BYTES = 131_072


def parser_one(code: str, *, opener=None) -> dict[str, object]:
    if code not in SOURCE_CODES:
        raise ValueError("source_not_authorized")
    url, _ = SOURCES[code]
    result: dict[str, object] = {
        "source": code, "http_code": None, "robots_status": "unverified",
        "result": "unavailable", "parser_records": 0, "declared_total": 0,
        "truncated": False, "sample_sha256": "", "corpus_validated": False,
        "media_downloaded": False,
    }
    opener = opener or build_opener(
        NoRedirect(), HTTPSHandler(context=ssl.create_default_context())
    )
    result["robots_status"] = robots_preflight(url, opener=opener)
    if result["robots_status"] != "robots_allowed":
        result["result"] = result["robots_status"]
        return result
    request = Request(url, headers={
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": USER_AGENT,
    })
    try:
        with opener.open(request, timeout=12) as response:
            result["http_code"] = response.status
            if response.status != 200:
                result["result"] = classify_http(response.status)
                return result
            if "html" not in response.headers.get("Content-Type", "").lower():
                result["result"] = "unexpected_content_type"
                return result
            sample = response.read(MAX_BYTES + 1)
    except HTTPError as error:
        result["http_code"] = error.code
        result["result"] = classify_http(error.code)
        return result
    except (URLError, TimeoutError, OSError):
        result["result"] = "public_network_unavailable"
        return result
    result["truncated"] = len(sample) > MAX_BYTES
    sample = sample[:MAX_BYTES]
    result["sample_sha256"] = hashlib.sha256(sample).hexdigest()
    html = sample.decode("utf-8", errors="replace")
    if code == "eye":
        # The original producer must declare the fragment filter: no
        # accidental materialization of unfiltered film catalogue entries.
        declared = extract_eye_declared_fragment_total(html)
        result["declared_total"] = declared
        if not declared or result["truncated"]:
            result["result"] = "eye_fragment_filter_not_proven"
            return result
        rows = parse_eye_fragment_list_page(html, url)
        result["parser_records"] = len(rows)
        result["result"] = (
            "eye_one_page_parser_pass"
            if rows else "eye_one_page_parser_no_records"
        )
    else:
        rows = parse_czech_television_catalog_page(html, "Cultura")
        result["parser_records"] = len(rows)
        result["result"] = (
            "czech_programme_candidates_only"
            if rows else "czech_parser_no_programmes"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCE_CODES), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"source": args.source, "mode": "offline_plan_only",
                          "corpus_validated": False}))
        return 0
    if os.environ.get("MAR_SOURCE_PROBE_APPROVED") != "yes":
        parser.error("Explicit GitHub label approval is required")
    print(json.dumps(parser_one(args.source), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
