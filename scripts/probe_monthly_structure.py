"""Opt-in structural sample of one public index per source (Eye or Czech TV).

Independent of corpus validation: no pagination, media, streams, follow-ups,
retries, API endpoints or persistent HTML. Fail closed on robots uncertainty.
"""
from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
import os
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, HTTPSHandler, build_opener

from scripts.probe_monthly_sources import (
    NoRedirect, SOURCES, USER_AGENT, classify_http, robots_preflight,
)

MAX_SAMPLE_BYTES = 131_072
ALLOWED = frozenset({"eye", "czech_tv"})


class PageTextAndLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = set()
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.add(value)

    def handle_data(self, data):
        self.text.append(data)


def structure_one(code: str, *, opener=None) -> dict[str, object]:
    if code not in ALLOWED:
        raise ValueError("source_not_authorized_for_structure_probe")
    url, _ = SOURCES[code]
    parsed = urlparse(url)
    answer: dict[str, object] = {
        "source": code, "url": url, "http_code": None,
        "robots_status": "unverified", "result": "unavailable",
        "sample_sha256": "", "bytes_sampled": 0, "truncated": False,
        "index_detail_candidates": 0, "filter_declared_total": 0,
        "corpus_validated": False,
    }
    opener = opener or build_opener(
        NoRedirect(), HTTPSHandler(context=ssl.create_default_context())
    )
    answer["robots_status"] = robots_preflight(url, opener=opener)
    if answer["robots_status"] != "robots_allowed":
        answer["result"] = answer["robots_status"]
        return answer
    request = Request(url, headers={
        "Accept": "text/html,application/xhtml+xml",
        "User-Agent": USER_AGENT,
    })
    try:
        with opener.open(request, timeout=12) as response:
            answer["http_code"] = response.status
            if response.status != 200:
                answer["result"] = classify_http(response.status)
                return answer
            if not any(x in response.headers.get("Content-Type", "").lower()
                       for x in ("text/html", "application/xhtml+xml")):
                answer["result"] = "unexpected_content_type"
                return answer
            data = response.read(MAX_SAMPLE_BYTES + 1)
    except HTTPError as e:
        answer["http_code"] = e.code
        answer["result"] = classify_http(e.code)
        return answer
    except (URLError, TimeoutError, OSError):
        answer["result"] = "public_network_unavailable"
        return answer

    answer["truncated"] = len(data) > MAX_SAMPLE_BYTES
    data = data[:MAX_SAMPLE_BYTES]
    answer["bytes_sampled"] = len(data)
    answer["sample_sha256"] = hashlib.sha256(data).hexdigest()
    markup = data.decode("utf-8", errors="replace")
    parser = PageTextAndLinks()
    parser.feed(markup)
    text = re.sub(r"\\s+", " ", " ".join(parser.text))

    allowed_links = set()
    for link in parser.hrefs:
        dest = urlparse(urljoin(url, link))
        if dest.scheme != "https" or dest.hostname != parsed.hostname:
            continue
        path = dest.path
        if code == "eye":
            if "/collection/film-history/film/" in path and not path.endswith("/all/all"):
                allowed_links.add(dest.geturl())
        elif re.match(r"^/porady/\\d{2,}-[a-z0-9-]+/?$", path, flags=re.I):
            allowed_links.add(dest.geturl())
    answer["index_detail_candidates"] = len(allowed_links)
    if code == "eye":
        match = re.search(
            r"with\\s+film\\s+fragment\\s*([0-9][0-9,.]*)",
            text, re.I,
        )
        if match:
            answer["filter_declared_total"] = int(
                re.sub(r"\\D", "", match.group(1)) or "0"
            )
        answer["result"] = (
            "fragment_index_candidates_only"
            if answer["filter_declared_total"] > 0 and allowed_links and not answer["truncated"]
            else "filter_or_index_unconfirmed"
        )
    else:
        answer["result"] = (
            "catalogue_programme_candidates_only"
            if allowed_links else "html_sample_needs_parser_review"
        )
    return answer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(ALLOWED), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({"source": args.source, "mode": "offline_plan_only",
                          "corpus_validated": False}))
        return 0
    if os.environ.get("MAR_SOURCE_PROBE_APPROVED") != "yes":
        parser.error("Live structural probe requires explicit approval")
    print(json.dumps(structure_one(args.source), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
