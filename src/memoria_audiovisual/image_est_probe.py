"""Fail-closed technical probe for Image'Est public film catalogue.

This probe inspects only public discovery and metadata surfaces. It never
downloads audiovisual media, never brute-forces identifiers, and never
authorizes corpus incorporation.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT


IMAGE_EST_HOME_URL = "https://www.image-est.fr/"
IMAGE_EST_ARCHIVE_URL = "https://www.image-est.fr/nos-archives-1283-0-0-0.html"
IMAGE_EST_FILMS_FILTER_URL = (
    "https://www.image-est.fr/js/ajax/diaPlugins/1283/ajax/add/type/1"
)
IMAGE_EST_ROBOTS_URL = "https://www.image-est.fr/robots.txt"
IMAGE_EST_PROBE_VERSION = "2026-10-image-est-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_ARCHIVE_PAGE_RE = re.compile(r"/nos-archives-1283-0-0-(\d+)\.html$", re.I)
_DETAIL_PATH_RE = re.compile(r"/fiche-documentaire-[^?#]+-1284-[^/?#]+\.html$", re.I)
_RESULT_COUNT_RE = re.compile(r"([0-9][0-9\s\u00a0\u202f.]*)\s+r[ée]sultat", re.I)
_FILM_LABELS = ("Année", "Durée", "Format", "Son", "Fonds")


@dataclass(frozen=True)
class ProbeResponse:
    requested_url: str
    final_url: str | None
    status_code: int | None
    content_type: str
    text: str
    error: str | None


def _clean(value: Any, *, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            **HEADERS,
            "User-Agent": f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-probe)",
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
        }
    )
    return session


def fetch_public_url(
    session: requests.Session,
    url: str,
    *,
    attempts: int = 3,
) -> ProbeResponse:
    response = None
    try:
        for attempt in range(attempts):
            response = session.get(
                url,
                timeout=(8, REQUEST_TIMEOUT),
                allow_redirects=True,
            )
            if response.status_code not in {429, 503}:
                break
            time.sleep(float(attempt + 1))
    except requests.RequestException as exc:
        return ProbeResponse(
            requested_url=url,
            final_url=getattr(response, "url", None),
            status_code=getattr(response, "status_code", None),
            content_type=(
                response.headers.get("content-type", "")
                if response is not None
                else ""
            ),
            text="",
            error=f"{type(exc).__name__}: {exc}",
        )
    return ProbeResponse(
        requested_url=url,
        final_url=response.url,
        status_code=response.status_code,
        content_type=response.headers.get("content-type", ""),
        text=response.text,
        error=None,
    )


def _robots_groups(text: str) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    saw_rule = False

    def flush() -> None:
        nonlocal agents, rules, saw_rule
        if agents:
            groups.append({"agents": tuple(agents), "rules": tuple(rules)})
        agents, rules, saw_rule = [], [], False

    for raw_line in (text or "").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip().lower(), value.strip()
        if key == "user-agent":
            if saw_rule:
                flush()
            agents.append(value.lower())
        elif key in {"allow", "disallow"} and agents:
            saw_rule = True
            if value:
                rules.append((key == "allow", value))
    flush()
    return groups


def _rule_regex(pattern: str) -> re.Pattern[str]:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    expression = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile("^" + expression + ("$" if anchored else ""))


def robots_allowed(text: str, user_agent: str, url: str) -> bool:
    groups = _robots_groups(text)
    agent = str(user_agent or "*").lower()
    explicit = [
        group
        for group in groups
        if any(
            token and token != "*" and token in agent
            for token in group["agents"]
        )
    ]
    selected = explicit or [group for group in groups if "*" in group["agents"]]
    if not selected:
        return True

    parsed = urlparse(url)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query

    matches: list[tuple[int, bool]] = []
    for group in selected:
        for allowance, pattern in group["rules"]:
            if _rule_regex(pattern).search(target):
                specificity = len(pattern.rstrip("$").replace("*", ""))
                matches.append((specificity, allowance))
    if not matches:
        return True
    longest = max(score for score, _ in matches)
    return any(allow for score, allow in matches if score == longest)


def evaluate_robots(
    session: requests.Session,
    targets: tuple[str, ...],
) -> tuple[dict[str, Any], str]:
    response = fetch_public_url(session, IMAGE_EST_ROBOTS_URL)
    result: dict[str, Any] = {
        "robots_url": IMAGE_EST_ROBOTS_URL,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
        "targets": [],
        "robots_excerpt": _clean(response.text, limit=1800),
    }
    robots_text = response.text or ""
    if response.error:
        result["mode"] = "unverifiable"
        reason = "robots_unreachable"
        fixed_allowed: bool | None = False
    elif response.status_code in {404, 410}:
        result["mode"] = "absent"
        reason = "robots_absent"
        fixed_allowed = True
    elif response.status_code != 200:
        result["mode"] = "unverifiable"
        reason = f"robots_http_{response.status_code}"
        fixed_allowed = False
    else:
        stripped = robots_text.strip()
        if not stripped or "<html" in stripped.lower():
            result["mode"] = "unverifiable"
            reason = "robots_invalid_payload"
            fixed_allowed = False
        else:
            result["mode"] = "evaluated_rfc9309"
            reason = "robots_evaluated_rfc9309"
            fixed_allowed = None

    for url in targets:
        allowed = (
            robots_allowed(robots_text, CRAWLER_TOKEN, url)
            if fixed_allowed is None
            else fixed_allowed
        )
        result["targets"].append(
            {"url": url, "allowed": bool(allowed), "reason": reason}
        )
    return result, robots_text


def parse_archive_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    match = _RESULT_COUNT_RE.search(text)
    result_count = None
    if match:
        digits = re.sub(r"\D", "", match.group(1))
        result_count = int(digits) if digits else None

    detail_links: list[str] = []
    pagination: list[dict[str, Any]] = []
    filter_links: list[str] = []
    seen_details: set[str] = set()
    seen_pages: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.netloc.lower() != "www.image-est.fr":
            continue

        if _DETAIL_PATH_RE.match(parsed.path) and absolute not in seen_details:
            seen_details.add(absolute)
            detail_links.append(absolute)

        page_match = _ARCHIVE_PAGE_RE.match(parsed.path)
        if page_match and absolute not in seen_pages:
            seen_pages.add(absolute)
            pagination.append(
                {
                    "url": absolute,
                    "page_number": int(page_match.group(1)),
                    "text": _clean(anchor.get_text(" ", strip=True), limit=80),
                }
            )

        if "/js/ajax/diaPlugins/1283/ajax/add/type/1" in parsed.path:
            filter_links.append(absolute)

    if IMAGE_EST_FILMS_FILTER_URL in html_text:
        filter_links.append(IMAGE_EST_FILMS_FILTER_URL)

    return {
        "title": _clean(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "result_count": result_count,
        "detail_links_count": len(detail_links),
        "detail_links": detail_links[:50],
        "pagination_links": sorted(
            pagination,
            key=lambda row: (row["page_number"], row["url"]),
        )[:100],
        "max_page_number": max(
            (row["page_number"] for row in pagination),
            default=None,
        ),
        "films_filter_links": sorted(set(filter_links)),
        "html_length": len(html_text or ""),
    }


def parse_detail_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    labels = [label for label in _FILM_LABELS if re.search(rf"\b{re.escape(label)}\b", text)]
    iframes = [
        urljoin(page_url, node.get("src", ""))
        for node in soup.find_all("iframe")
        if node.get("src")
    ]
    title_node = soup.find("h1")
    return {
        "title": _clean(title_node.get_text(" ", strip=True) if title_node else ""),
        "labels": labels,
        "label_count": len(labels),
        "iframe_urls": iframes[:10],
        "film_semantics_confirmed": len(labels) >= 3 and bool(iframes),
    }


def _select_bounded_pages(parsed: dict[str, Any]) -> list[str]:
    rows = parsed.get("pagination_links", [])
    if not rows:
        return []
    by_page = {int(row["page_number"]): row["url"] for row in rows}
    page_numbers = sorted(by_page)
    selected: list[int] = []
    for candidate in page_numbers:
        if candidate > 0:
            selected.append(candidate)
            break
    if page_numbers[-1] not in selected:
        selected.append(page_numbers[-1])
    return [by_page[number] for number in selected[:2]]


def run_image_est_probe(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()
    targets = (
        IMAGE_EST_HOME_URL,
        IMAGE_EST_ARCHIVE_URL,
        IMAGE_EST_FILMS_FILTER_URL,
    )
    robots, robots_text = evaluate_robots(session, targets)
    allowed_map = {
        row["url"]: bool(row["allowed"])
        for row in robots.get("targets", [])
    }

    result: dict[str, Any] = {
        "probe_version": IMAGE_EST_PROBE_VERSION,
        "automatic_incorporation_authorized": False,
        "brute_force_id_scan_performed": False,
        "media_download_performed": False,
        "experimental_model_used": False,
        "custodial_film_count_context_only": 30000,
        "custodial_count_used_as_web_denominator": False,
        "robots": robots,
        "archive_surface": None,
        "films_filter": None,
        "bounded_pages": [],
        "detail_samples": [],
        "gate_assessment": "hold_unresolved",
        "next_action": "protocol_hold_or_retest",
    }

    if not all(allowed_map.get(url, False) for url in targets):
        result["gate_assessment"] = "hold_robots_not_allowed_or_unverifiable"
        return result

    archive_response = fetch_public_url(session, IMAGE_EST_ARCHIVE_URL)
    archive_parsed = (
        parse_archive_html(archive_response.text, archive_response.final_url or IMAGE_EST_ARCHIVE_URL)
        if archive_response.status_code == 200 and not archive_response.error
        else {}
    )
    result["archive_surface"] = {
        "requested_url": IMAGE_EST_ARCHIVE_URL,
        "final_url": archive_response.final_url,
        "status_code": archive_response.status_code,
        "error": archive_response.error,
        "parsed": archive_parsed,
    }

    filter_discovered = IMAGE_EST_FILMS_FILTER_URL in archive_parsed.get(
        "films_filter_links", []
    )
    if not filter_discovered:
        result["gate_assessment"] = "hold_films_filter_not_discovered_in_public_html"
        return result

    filter_response = fetch_public_url(session, IMAGE_EST_FILMS_FILTER_URL)
    filter_parsed = (
        parse_archive_html(
            filter_response.text,
            filter_response.final_url or IMAGE_EST_FILMS_FILTER_URL,
        )
        if filter_response.status_code == 200 and not filter_response.error
        else {}
    )
    result["films_filter"] = {
        "requested_url": IMAGE_EST_FILMS_FILTER_URL,
        "final_url": filter_response.final_url,
        "status_code": filter_response.status_code,
        "error": filter_response.error,
        "parsed": filter_parsed,
    }

    if (
        filter_response.status_code != 200
        or filter_response.error
        or not filter_parsed.get("result_count")
        or not filter_parsed.get("detail_links_count")
    ):
        result["gate_assessment"] = "hold_video_filter_not_reproducible"
        return result

    first_details = set(filter_parsed.get("detail_links", []))
    page_urls = _select_bounded_pages(filter_parsed)
    page_sets: list[set[str]] = [first_details]
    counts = [filter_parsed["result_count"]]

    for page_url in page_urls:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, page_url):
            result["bounded_pages"].append(
                {"url": page_url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(session, page_url)
        parsed = (
            parse_archive_html(response.text, response.final_url or page_url)
            if response.status_code == 200 and not response.error
            else {}
        )
        result["bounded_pages"].append(
            {
                "url": page_url,
                "final_url": response.final_url,
                "status_code": response.status_code,
                "error": response.error,
                "parsed": parsed,
            }
        )
        page_sets.append(set(parsed.get("detail_links", [])))
        counts.append(parsed.get("result_count"))

    sample_detail_urls = list(filter_parsed.get("detail_links", [])[:2])
    for detail_url in sample_detail_urls:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, detail_url):
            result["detail_samples"].append(
                {"url": detail_url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(session, detail_url)
        semantics = (
            parse_detail_html(response.text, response.final_url or detail_url)
            if response.status_code == 200 and not response.error
            else {
                "title": "",
                "labels": [],
                "label_count": 0,
                "iframe_urls": [],
                "film_semantics_confirmed": False,
            }
        )
        result["detail_samples"].append(
            {
                "url": detail_url,
                "status_code": response.status_code,
                "error": response.error,
                **semantics,
            }
        )

    page_samples_ok = (
        len(result["bounded_pages"]) >= 2
        and all(
            row.get("status_code") == 200
            and not row.get("error")
            and row.get("parsed", {}).get("detail_links_count", 0) > 0
            for row in result["bounded_pages"]
        )
    )
    stable_count = (
        len(counts) >= 3
        and all(count == counts[0] and count for count in counts)
    )
    distinct_pages = (
        len(page_sets) >= 3
        and all(page_sets)
        and all(
            page_sets[index].isdisjoint(page_sets[other])
            for index in range(len(page_sets))
            for other in range(index + 1, len(page_sets))
        )
    )
    detail_semantics_ok = (
        len(result["detail_samples"]) == 2
        and all(row.get("film_semantics_confirmed") for row in result["detail_samples"])
    )

    result["bounded_enumeration"] = {
        "public_reported_video_results": filter_parsed.get("result_count"),
        "bounded_page_samples_ok": page_samples_ok,
        "stable_reported_count": stable_count,
        "distinct_detail_permalink_sets": distinct_pages,
        "detail_semantics_confirmed": detail_semantics_ok,
        "selected_page_urls": page_urls,
    }

    if page_samples_ok and stable_count and distinct_pages and detail_semantics_ok:
        result["gate_assessment"] = (
            "bounded_video_catalogue_enumeration_confirmed_staged_required"
        )
        result["next_action"] = "engineer_full_staged_enumeration_with_integrity_gates"
    else:
        result["gate_assessment"] = "hold_bounded_enumeration_not_yet_reproducible"
    return result


def dumps_probe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "IMAGE_EST_ARCHIVE_URL",
    "IMAGE_EST_FILMS_FILTER_URL",
    "IMAGE_EST_HOME_URL",
    "IMAGE_EST_ROBOTS_URL",
    "parse_archive_html",
    "parse_detail_html",
    "robots_allowed",
    "run_image_est_probe",
]
