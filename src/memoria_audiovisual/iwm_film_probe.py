"""Fail-closed technical probe for the public IWM Film catalogue.

The probe discovers public catalogue mechanisms without guessing record IDs,
downloading media, or authorizing corpus incorporation.
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


IWM_FILM_HOME_URL = "https://film.iwmcollections.org.uk/"
IWM_FILM_SEARCH_URL = "https://film.iwmcollections.org.uk/search/results"
IWM_FILM_CATEGORIES_URL = "https://film.iwmcollections.org.uk/conflict_categories"
IWM_FILM_FAQ_URL = "https://film.iwmcollections.org.uk/faqs"
IWM_FILM_ROBOTS_URL = "https://film.iwmcollections.org.uk/robots.txt"
IWM_FILM_PROBE_VERSION = "2026-10-iwm-film-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_ALLOWED_HOST = "film.iwmcollections.org.uk"
_RECORD_PATH_RE = re.compile(r"^/record/(\d+)/?$", re.I)
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_SITEMAP_DIRECTIVE_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")
_ENDPOINT_HINT_RE = re.compile(
    r"""(?P<quote>["'])(?P<value>/[^"'\s]{2,180}(?:search|api|record|graphql|query)[^"'\s]{0,180})(?P=quote)""",
    re.I,
)
_RECORD_LABELS = (
    "Film Number",
    "Digitised",
    "Production Date",
    "Production Country",
    "Sound",
    "Physical Characteristics",
    "Technical Details",
)


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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-GB,en;q=0.9",
        }
    )
    return session


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
    explicit_matches: list[tuple[int, dict[str, Any]]] = []
    for group in groups:
        lengths = [
            len(token)
            for token in group["agents"]
            if token and token != "*" and token in agent
        ]
        if lengths:
            explicit_matches.append((max(lengths), group))

    if explicit_matches:
        longest = max(length for length, _ in explicit_matches)
        selected = [group for length, group in explicit_matches if length == longest]
    else:
        selected = [group for group in groups if "*" in group["agents"]]
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
                score = len(pattern.rstrip("$").replace("*", ""))
                matches.append((score, allowance))
    if not matches:
        return True
    longest_rule = max(score for score, _ in matches)
    return any(allow for score, allow in matches if score == longest_rule)


def fetch_public_url(
    session: requests.Session,
    url: str,
    *,
    robots_text: str | None = None,
    attempts: int = 3,
    max_redirects: int = 5,
) -> ProbeResponse:
    requested_url = url
    current_url = url
    response = None

    for _ in range(max_redirects + 1):
        parsed = urlparse(current_url)
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != _ALLOWED_HOST:
            return ProbeResponse(
                requested_url=requested_url,
                final_url=current_url,
                status_code=getattr(response, "status_code", None),
                content_type="",
                text="",
                error="redirect_target_outside_authorized_origin",
            )
        if robots_text is not None and not robots_allowed(
            robots_text, CRAWLER_TOKEN, current_url
        ):
            return ProbeResponse(
                requested_url=requested_url,
                final_url=current_url,
                status_code=getattr(response, "status_code", None),
                content_type="",
                text="",
                error="redirect_target_blocked_by_robots",
            )

        try:
            for attempt in range(attempts):
                response = session.get(
                    current_url,
                    timeout=(8, REQUEST_TIMEOUT),
                    allow_redirects=False,
                )
                if response.status_code not in {429, 503}:
                    break
                time.sleep(float(attempt + 1))
        except requests.RequestException as exc:
            return ProbeResponse(
                requested_url=requested_url,
                final_url=current_url,
                status_code=getattr(response, "status_code", None),
                content_type=(
                    response.headers.get("content-type", "")
                    if response is not None
                    else ""
                ),
                text="",
                error=f"{type(exc).__name__}: {exc}",
            )

        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("location", "")
            if not location:
                return ProbeResponse(
                    requested_url=requested_url,
                    final_url=current_url,
                    status_code=response.status_code,
                    content_type=response.headers.get("content-type", ""),
                    text="",
                    error="redirect_without_location",
                )
            current_url = urljoin(current_url, location)
            continue

        return ProbeResponse(
            requested_url=requested_url,
            final_url=current_url,
            status_code=response.status_code,
            content_type=response.headers.get("content-type", ""),
            text=response.text,
            error=None,
        )

    return ProbeResponse(
        requested_url=requested_url,
        final_url=current_url,
        status_code=getattr(response, "status_code", None),
        content_type="",
        text="",
        error="redirect_limit_exceeded",
    )


def evaluate_robots(
    session: requests.Session,
    targets: tuple[str, ...],
) -> tuple[dict[str, Any], str]:
    response = fetch_public_url(session, IWM_FILM_ROBOTS_URL)
    result: dict[str, Any] = {
        "robots_url": IWM_FILM_ROBOTS_URL,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
        "targets": [],
        "sitemaps": [],
        "robots_excerpt": _clean(response.text, limit=2000),
    }
    robots_text = response.text or ""
    result["sitemaps"] = sorted(set(_SITEMAP_DIRECTIVE_RE.findall(robots_text)))

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


def parse_surface_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    records: list[str] = []
    scripts: list[str] = []
    same_host_links: list[str] = []
    forms: list[dict[str, Any]] = []

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.netloc.lower() != _ALLOWED_HOST:
            continue
        if absolute not in same_host_links:
            same_host_links.append(absolute)
        if _RECORD_PATH_RE.match(parsed.path) and absolute not in records:
            records.append(absolute)

    for script in soup.find_all("script", src=True):
        absolute = urljoin(page_url, script.get("src", ""))
        parsed = urlparse(absolute)
        if parsed.netloc.lower() == _ALLOWED_HOST and absolute not in scripts:
            scripts.append(absolute)

    for form in soup.find_all("form"):
        action = urljoin(page_url, form.get("action", ""))
        parsed = urlparse(action)
        inputs = sorted(
            {
                str(node.get("name", "")).strip()
                for node in form.find_all(["input", "select", "textarea"])
                if str(node.get("name", "")).strip()
            }
        )
        forms.append(
            {
                "method": str(form.get("method", "get")).upper(),
                "action": action if parsed.netloc.lower() == _ALLOWED_HOST else "",
                "input_names": inputs[:50],
            }
        )

    inline_text = "\n".join(
        script.get_text("\n", strip=False)
        for script in soup.find_all("script")
        if not script.get("src")
    )
    endpoint_hints = sorted(
        {
            urljoin(page_url, match.group("value"))
            for match in _ENDPOINT_HINT_RE.finditer(inline_text)
            if urlparse(urljoin(page_url, match.group("value"))).netloc.lower()
            == _ALLOWED_HOST
        }
    )

    visible_text = _clean(soup.get_text(" ", strip=True), limit=5000)
    return {
        "title": _clean(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "record_links": records[:100],
        "record_links_count": len(records),
        "same_host_links": same_host_links[:100],
        "forms": forms[:20],
        "script_urls": scripts[:50],
        "inline_endpoint_hints": endpoint_hints[:100],
        "requires_javascript_message": "requires JavaScript" in visible_text,
        "unable_to_search_message": "Unable to search at this time" in visible_text,
        "html_length": len(html_text or ""),
    }


def parse_script_hints(script_text: str, base_url: str) -> dict[str, Any]:
    endpoints = sorted(
        {
            urljoin(base_url, match.group("value"))
            for match in _ENDPOINT_HINT_RE.finditer(script_text or "")
            if urlparse(urljoin(base_url, match.group("value"))).netloc.lower()
            == _ALLOWED_HOST
        }
    )
    record_paths = sorted(
        {
            urljoin(base_url, value)
            for value in re.findall(r'["\'](/record/\d+/?)["\']', script_text or "")
        }
    )
    return {
        "endpoint_hints": endpoints[:100],
        "record_links": record_paths[:100],
        "script_length": len(script_text or ""),
    }


def parse_sitemap(xml_text: str) -> dict[str, Any]:
    urls = [_clean(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    records = []
    nested = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.netloc.lower() != _ALLOWED_HOST:
            continue
        if _RECORD_PATH_RE.match(parsed.path):
            records.append(url)
        elif parsed.path.lower().endswith(".xml"):
            nested.append(url)
    return {
        "url_count": len(urls),
        "record_links_count": len(set(records)),
        "record_links": sorted(set(records))[:100],
        "nested_sitemaps": sorted(set(nested))[:50],
    }


def parse_record_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    labels = [
        label
        for label in _RECORD_LABELS
        if re.search(rf"\b{re.escape(label)}\b", text, re.I)
    ]
    title_node = soup.find("h1")
    digitised_match = re.search(r"Digitised\s*:\s*(Yes|No)", text, re.I)
    media_markers = [
        marker
        for marker in ("Media files", "Video", "Media not currently available")
        if marker.lower() in text.lower()
    ]
    return {
        "url": page_url,
        "title": _clean(title_node.get_text(" ", strip=True) if title_node else ""),
        "labels": labels,
        "label_count": len(labels),
        "digitised": digitised_match.group(1).lower() if digitised_match else "",
        "media_markers": media_markers,
        "film_semantics_confirmed": (
            "Film Number" in labels
            and "Digitised" in labels
            and len(labels) >= 4
        ),
    }


def run_iwm_film_probe(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()
    targets = (
        IWM_FILM_HOME_URL,
        IWM_FILM_SEARCH_URL,
        IWM_FILM_CATEGORIES_URL,
        IWM_FILM_FAQ_URL,
    )
    robots, robots_text = evaluate_robots(session, targets)
    allowed_map = {
        row["url"]: bool(row["allowed"])
        for row in robots.get("targets", [])
    }

    result: dict[str, Any] = {
        "probe_version": IWM_FILM_PROBE_VERSION,
        "automatic_incorporation_authorized": False,
        "brute_force_id_scan_performed": False,
        "record_id_range_inferred": False,
        "media_download_performed": False,
        "authenticated_download_attempted": False,
        "custodial_footage_hours_context_only": 25000,
        "custodial_count_used_as_web_denominator": False,
        "robots": robots,
        "surfaces": [],
        "script_probes": [],
        "sitemaps": [],
        "record_samples": [],
        "enumeration_mechanisms": [],
        "gate_assessment": "hold_unresolved",
        "next_action": "protocol_hold_or_retest",
    }

    if not all(allowed_map.get(url, False) for url in targets):
        result["gate_assessment"] = "hold_robots_not_allowed_or_unverifiable"
        return result

    discovered_records: set[str] = set()
    discovered_scripts: list[str] = []
    discovered_endpoint_hints: set[str] = set()

    for kind, url in (
        ("home", IWM_FILM_HOME_URL),
        ("search", IWM_FILM_SEARCH_URL),
        ("categories", IWM_FILM_CATEGORIES_URL),
        ("faq", IWM_FILM_FAQ_URL),
    ):
        response = fetch_public_url(session, url, robots_text=robots_text)
        parsed = (
            parse_surface_html(response.text, response.final_url or url)
            if response.status_code == 200 and not response.error
            else {}
        )
        result["surfaces"].append(
            {
                "kind": kind,
                "requested_url": url,
                "final_url": response.final_url,
                "status_code": response.status_code,
                "error": response.error,
                "parsed": parsed,
            }
        )
        discovered_records.update(parsed.get("record_links", []))
        discovered_endpoint_hints.update(parsed.get("inline_endpoint_hints", []))
        for script_url in parsed.get("script_urls", []):
            if script_url not in discovered_scripts:
                discovered_scripts.append(script_url)

    for script_url in discovered_scripts[:4]:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, script_url):
            result["script_probes"].append(
                {"url": script_url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(
            session, script_url, robots_text=robots_text
        )
        hints = (
            parse_script_hints(response.text, response.final_url or script_url)
            if response.status_code == 200 and not response.error
            else {}
        )
        result["script_probes"].append(
            {
                "url": script_url,
                "status_code": response.status_code,
                "error": response.error,
                "hints": hints,
            }
        )
        discovered_records.update(hints.get("record_links", []))
        discovered_endpoint_hints.update(hints.get("endpoint_hints", []))

    for sitemap_url in robots.get("sitemaps", [])[:4]:
        parsed_url = urlparse(sitemap_url)
        if parsed_url.scheme.lower() != "https" or parsed_url.netloc.lower() != _ALLOWED_HOST:
            result["sitemaps"].append(
                {"url": sitemap_url, "status": "outside_authorized_origin"}
            )
            continue
        if not robots_allowed(robots_text, CRAWLER_TOKEN, sitemap_url):
            result["sitemaps"].append(
                {"url": sitemap_url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(
            session, sitemap_url, robots_text=robots_text
        )
        parsed = (
            parse_sitemap(response.text)
            if response.status_code == 200 and not response.error
            else {}
        )
        result["sitemaps"].append(
            {
                "url": sitemap_url,
                "status_code": response.status_code,
                "error": response.error,
                "parsed": parsed,
            }
        )
        discovered_records.update(parsed.get("record_links", []))

    record_urls = sorted(discovered_records)
    for record_url in record_urls[:2]:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, record_url):
            result["record_samples"].append(
                {"url": record_url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(
            session, record_url, robots_text=robots_text
        )
        parsed = (
            parse_record_html(response.text, response.final_url or record_url)
            if response.status_code == 200 and not response.error
            else {}
        )
        result["record_samples"].append(
            {
                "requested_url": record_url,
                "final_url": response.final_url,
                "status_code": response.status_code,
                "error": response.error,
                "parsed": parsed,
            }
        )

    search_surface = next(
        (row for row in result["surfaces"] if row["kind"] == "search"),
        {},
    )
    search_parsed = search_surface.get("parsed") or {}
    search_forms = [
        form
        for row in result["surfaces"]
        for form in (row.get("parsed") or {}).get("forms", [])
        if "/search" in form.get("action", "")
    ]
    sitemap_record_count = sum(
        int((row.get("parsed") or {}).get("record_links_count", 0))
        for row in result["sitemaps"]
    )

    if search_forms or search_surface.get("status_code") == 200:
        result["enumeration_mechanisms"].append("public_search_surface")
    if discovered_endpoint_hints:
        result["enumeration_mechanisms"].append(
            "published_script_endpoint_hints_not_executed"
        )
    if sitemap_record_count:
        result["enumeration_mechanisms"].append(
            "robots_declared_sitemap_with_record_permalinks"
        )

    result["discovery_summary"] = {
        "search_forms_count": len(search_forms),
        "search_requires_javascript": bool(
            search_parsed.get("requires_javascript_message")
        ),
        "search_unavailable_server_side": bool(
            search_parsed.get("unable_to_search_message")
        ),
        "same_host_scripts_discovered": len(discovered_scripts),
        "endpoint_hints_discovered": sorted(discovered_endpoint_hints)[:100],
        "record_permalinks_discovered": len(record_urls),
        "sitemap_record_permalinks_discovered": sitemap_record_count,
        "sampled_record_count": len(result["record_samples"]),
        "sampled_record_semantics_confirmed": all(
            (row.get("parsed") or {}).get("film_semantics_confirmed", False)
            for row in result["record_samples"]
        )
        if result["record_samples"]
        else False,
    }

    if sitemap_record_count and result["discovery_summary"][
        "sampled_record_semantics_confirmed"
    ]:
        result["gate_assessment"] = (
            "bounded_public_record_enumeration_confirmed_staged_required"
        )
        result["next_action"] = (
            "engineer_full_staged_enumeration_from_declared_sitemap"
        )
    elif search_forms or search_surface.get("status_code") == 200:
        result["gate_assessment"] = (
            "public_search_surface_confirmed_enumeration_not_yet_validated"
        )
        result["next_action"] = (
            "inspect_published_search_mechanism_without_guessing_endpoints"
        )
    else:
        result["gate_assessment"] = (
            "hold_no_reproducible_enumeration_surface_detected"
        )
    return result


def dumps_probe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


__all__ = [
    "IWM_FILM_CATEGORIES_URL",
    "IWM_FILM_FAQ_URL",
    "IWM_FILM_HOME_URL",
    "IWM_FILM_ROBOTS_URL",
    "IWM_FILM_SEARCH_URL",
    "parse_record_html",
    "parse_script_hints",
    "parse_surface_html",
    "robots_allowed",
    "run_iwm_film_probe",
]
