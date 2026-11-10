"""Opt-in, one-source public metadata availability probe (robots + one page).

Not a collector: no pagination, videos, downloads or API authentication.\nInspect robots.txt first; inaccessible or disallowing robots fail closed.
No default live network operation. Diagnostic findings are not corpus success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from urllib.request import (
    HTTPRedirectHandler,
    HTTPSHandler,
    Request,
    build_opener,
)

MAX_BYTES = 131_072
ROBOTS_MAX_BYTES = 65_536
USER_AGENT = 'MAR-Research-AvailabilityProbe/1.0'
SOURCES = {
    "ape": (
        "https://www.archivesportaleurope.net/find-an-institution/",
        "Search in institutions",
    ),
    "asim": (
        "https://www.europeanfilmgateway.eu/search-efg/Arxiu%20del%20So%20i%20de%20la%20Imatge%20de%20Mallorca",
        "ASIM",
    ),
    "barch": (
        "https://www.europeanfilmgateway.eu/search-efg/bundesarchiv",
        "Bundesarchiv",
    ),
    "bnfa": (
        "https://www.europeanfilmgateway.eu/search-efg/bnfa",
        "Bulgarian National Film Archive",
    ),
    "ciclic": (
        "https://memoire.ciclic.fr/films-d-archives",
        "Films d'archives",
    ),
    "czech_tv": (
        "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/",
        "Kultura",
    ),
    "eye": (
        "https://filmdatabase.eyefilm.nl/en/collection/film-history/film/all/all?f%5B0%5D=field_cm_media_filter%3Awith%20film%20fragment",
        "film",
    ),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def classify_http(status: int) -> str:
    if status == 403:
        return "source_access_forbidden"
    if status == 429:
        return "source_rate_limited"
    if status in (301, 302, 303, 307, 308):
        return "source_redirect_requires_review"
    if status >= 400:
        return "source_http_error"
    return "http_ok_not_proof_of_corpus"


def robots_preflight(url: str, *, opener) -> str:
    """Use one bounded same-origin robots.txt request, fail closed on ambiguity.

    An inaccessible robots.txt never authorizes a catalogue probe. No redirects
    or further links are followed; this preflight is only a safety signal.
    """
    parsed = urlparse(url)
    robots_url = urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))
    request = Request(
        robots_url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain"},
    )
    try:
        with opener.open(request, timeout=12) as response:
            if response.status != 200:
                return "robots_unavailable"
            sample = response.read(ROBOTS_MAX_BYTES + 1)
            if len(sample) > ROBOTS_MAX_BYTES or b"\\x00" in sample:
                return "robots_unusable"
            # Parse only a bounded text response, never execute fetched content.
            rules = RobotFileParser()
            rules.parse(sample.decode("utf-8", errors="replace").splitlines())
            return "robots_allowed" if rules.can_fetch(USER_AGENT, url) else "robots_disallowed"
    except (HTTPError, URLError, TimeoutError, OSError):
        return "robots_unavailable"


def probe_one(code: str, *, opener=None) -> dict[str, object]:
    if code not in SOURCES:
        raise ValueError("source_not_allowlisted")
    url, marker = SOURCES[code]
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username:
        raise ValueError("source_url_not_trusted")
    answer: dict[str, object] = {
        "source": code,
        "url": url,
        "result": "unavailable",
        "http_code": None,
        "marker_found": False,
        "bytes_sampled": 0,
        "sample_sha256": "",
        "corpus_validated": False,
        "robots_status": "unverified",
    }
    opener = opener or build_opener(
        NoRedirect(), HTTPSHandler(context=ssl.create_default_context())
    )
    answer["robots_status"] = robots_preflight(url, opener=opener)
    if answer["robots_status"] != "robots_allowed":
        answer["result"] = answer["robots_status"]
        return answer
    request = Request(
        url,
        headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": USER_AGENT,
        },
    )
    try:
        with opener.open(request, timeout=12) as response:
            status = response.status
            answer["http_code"] = status
            answer["result"] = classify_http(status)
            content_type = response.headers.get("Content-Type", "").lower()
            if not ("text/html" in content_type or "application/xhtml+xml" in content_type):
                answer["result"] = "unexpected_content_type"
                return answer
            # One bounded HTML sample, never images/video/PDF/multimedia.
            sample = response.read(MAX_BYTES + 1)
            if len(sample) > MAX_BYTES:
                answer["result"] = "oversize_html_sample"
                return answer
            answer["bytes_sampled"] = len(sample)
            answer["sample_sha256"] = hashlib.sha256(sample).hexdigest()
            answer["marker_found"] = marker.casefold().encode() in sample.lower()
            if not answer["marker_found"]:
                answer["result"] = "html_marker_absent_needs_parser_review"
    except HTTPError as error:
        answer["http_code"] = error.code
        answer["result"] = classify_http(error.code)
    except (URLError, OSError, TimeoutError):
        # Never print exception details (network URLs/credentials).
        answer["result"] = "public_network_unavailable"
    return answer


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=sorted(SOURCES), required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps({
            "source": args.source,
            "url": SOURCES[args.source][0],
            "mode": "offline_plan_only",
            "corpus_validated": False,
        }, ensure_ascii=False))
        return 0
    if os.environ.get("MAR_SOURCE_PROBE_APPROVED") != "yes":
        parser.error("Live probe requires explicit MAR_SOURCE_PROBE_APPROVED=yes")
    print(json.dumps(probe_one(args.source), ensure_ascii=False, sort_keys=True))
    return 0  # A probe never publishes corpus data or gates production.


if __name__ == "__main__":
    raise SystemExit(main())
