"""Technical, non-invasive probe for the public Gosfilmofond catalogue.

This module is deliberately not a corpus collector. It inspects the public
catalogue surface, robots policy, sitemaps and openly exposed WordPress/REST
metadata in order to determine whether a reproducible enumeration route exists.

No brute-force ID scanning is performed and no experimental MAR classifier is
used. The output is evidence for a later corpus-admission decision.
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


GOSFILMOFOND_HOME_URL = "https://gosfilmofond.ru/"
GOSFILMOFOND_CATALOG_URL = "https://gosfilmofond.ru/films/"
GOSFILMOFOND_ROBOTS_URL = "https://gosfilmofond.ru/robots.txt"
GOSFILMOFOND_SITEMAP_CANDIDATES = (
    "https://gosfilmofond.ru/wp-sitemap.xml",
    "https://gosfilmofond.ru/sitemap_index.xml",
    "https://gosfilmofond.ru/sitemap.xml",
)
GOSFILMOFOND_REST_ROOT = "https://gosfilmofond.ru/wp-json/"
GOSFILMOFOND_PROBE_VERSION = "2026-10-gosfilmofond-probe-v1"

_FILM_PATH_RE = re.compile(r"^/films/(?:[A-Za-z0-9._~%+-]+/)?$")
_FILM_DETAIL_RE = re.compile(r"^/films/([^/?#]+)/?$")
_DISCOVERY_TOKEN_RE = re.compile(
    r"(?:admin-ajax|wp-json|rest_url|ajaxurl|graphql|api/|load_more|load-more|"
    r"pagination|paged|page_num|posts_per_page|films?)",
    re.I,
)
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)


@dataclass(frozen=True)
class ProbeResponse:
    requested_url: str
    final_url: str | None
    status_code: int | None
    content_type: str
    text: str
    error: str | None


def _clean_text(value: Any, *, limit: int | None = None) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            **HEADERS,
            "Accept": "text/html,application/xhtml+xml,application/json,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
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
            time.sleep(1.0 * (attempt + 1))
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
    """Parse groups while preserving '?' and '*' in path patterns."""
    groups: list[dict[str, Any]] = []
    agents: list[str] = []
    rules: list[tuple[bool, str]] = []
    saw_rule = False

    def flush() -> None:
        nonlocal agents, rules, saw_rule
        if agents:
            groups.append({"agents": tuple(agents), "rules": tuple(rules)})
        agents = []
        rules = []
        saw_rule = False

    for raw_line in (text or "").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "user-agent":
            if saw_rule:
                flush()
            agents.append(value.lower())
            continue
        if key not in {"allow", "disallow"} or not agents:
            continue
        saw_rule = True
        if value:
            rules.append((key == "allow", value))
    flush()
    return groups


def _robots_rule_regex(pattern: str) -> re.Pattern[str]:
    anchored = pattern.endswith("$")
    body = pattern[:-1] if anchored else pattern
    expression = ".*".join(re.escape(part) for part in body.split("*"))
    return re.compile("^" + expression + ("$" if anchored else ""))


def _robots_rule_specificity(pattern: str) -> int:
    return len(pattern.rstrip("$").replace("*", ""))


def robots_allowed_rfc9309(text: str, user_agent: str, url: str) -> bool:
    """Apply RFC 9309-style longest-match semantics to common REP patterns."""
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
    selected = explicit or [
        group for group in groups if "*" in group["agents"]
    ]
    if not selected:
        return True

    parsed = urlparse(url)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query

    matches: list[tuple[int, bool]] = []
    for group in selected:
        for allowance, pattern in group["rules"]:
            if _robots_rule_regex(pattern).search(target):
                matches.append(
                    (_robots_rule_specificity(pattern), allowance)
                )
    if not matches:
        return True
    longest = max(score for score, _ in matches)
    finalists = [
        allowance for score, allowance in matches if score == longest
    ]
    return any(finalists)


def evaluate_robots(
    session: requests.Session,
    target_urls: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    response = fetch_public_url(session, GOSFILMOFOND_ROBOTS_URL)
    result: dict[str, Any] = {
        "robots_url": GOSFILMOFOND_ROBOTS_URL,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
        "targets": [],
        "robots_excerpt": _clean_text(response.text, limit=1800),
    }
    if response.error:
        result["mode"] = "unverifiable"
        for url in target_urls:
            result["targets"].append(
                {"url": url, "allowed": False, "reason": "robots_unreachable"}
            )
        return result
    if response.status_code in {404, 410}:
        result["mode"] = "absent"
        for url in target_urls:
            result["targets"].append(
                {"url": url, "allowed": True, "reason": "robots_absent"}
            )
        return result
    if response.status_code != 200:
        result["mode"] = "unverifiable"
        for url in target_urls:
            result["targets"].append(
                {
                    "url": url,
                    "allowed": False,
                    "reason": f"robots_http_{response.status_code}",
                }
            )
        return result

    user_agent = session.headers.get("User-Agent", "*")
    result["mode"] = "evaluated_rfc9309"
    for url in target_urls:
        result["targets"].append(
            {
                "url": url,
                "allowed": robots_allowed_rfc9309(
                    response.text,
                    user_agent,
                    url,
                ),
                "reason": "robots_evaluated_rfc9309",
            }
        )
    return result


def _allowed_map(robots: dict[str, Any]) -> dict[str, bool]:
    return {
        row["url"]: bool(row["allowed"])
        for row in robots.get("targets", [])
        if isinstance(row, dict) and row.get("url")
    }


def parse_catalog_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")

    film_links: list[dict[str, str]] = []
    seen_film_urls: set[str] = set()
    pagination_links: list[str] = []
    seen_pagination: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.netloc.endswith("gosfilmofond.ru"):
            detail = _FILM_DETAIL_RE.match(parsed.path)
            if detail and parsed.path.rstrip("/") != "/films":
                if absolute not in seen_film_urls:
                    seen_film_urls.add(absolute)
                    film_links.append(
                        {
                            "url": absolute,
                            "record_key": detail.group(1),
                            "anchor_text": _clean_text(
                                anchor.get_text(" ", strip=True),
                                limit=300,
                            ),
                        }
                    )
            rel = " ".join(anchor.get("rel", []))
            cls = " ".join(anchor.get("class", []))
            marker = f"{rel} {cls} {anchor.get_text(' ', strip=True)}"
            if re.search(r"next|prev|page|pagination|след|назад|далее", marker, re.I):
                if absolute not in seen_pagination:
                    seen_pagination.add(absolute)
                    pagination_links.append(absolute)

    forms = []
    for form in soup.find_all("form"):
        controls = []
        for node in form.find_all(["input", "select", "textarea", "button"]):
            name = _clean_text(node.get("name") or node.get("id"))
            node_type = _clean_text(node.get("type") or node.name)
            value = _clean_text(node.get("value"), limit=200)
            if name or value:
                controls.append(
                    {
                        "name": name,
                        "type": node_type,
                        "value": value,
                    }
                )
        forms.append(
            {
                "action": urljoin(page_url, form.get("action") or page_url),
                "method": _clean_text(form.get("method") or "get").lower(),
                "controls": controls[:80],
            }
        )

    scripts = []
    inline_discovery = []
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            scripts.append(urljoin(page_url, src))
        inline = script.string or script.get_text(" ", strip=True)
        if inline and _DISCOVERY_TOKEN_RE.search(inline):
            matches = sorted(
                set(
                    _clean_text(match.group(0))
                    for match in _DISCOVERY_TOKEN_RE.finditer(inline)
                )
            )
            inline_discovery.append(
                {
                    "tokens": matches[:20],
                    "excerpt": _clean_text(inline, limit=1200),
                }
            )

    data_hints = []
    for node in soup.find_all(True):
        for key, value in node.attrs.items():
            if not str(key).startswith("data-"):
                continue
            rendered = " ".join(value) if isinstance(value, list) else str(value)
            if _DISCOVERY_TOKEN_RE.search(f"{key} {rendered}"):
                data_hints.append(
                    {
                        "tag": node.name,
                        "attribute": str(key),
                        "value": _clean_text(rendered, limit=500),
                    }
                )

    return {
        "title": _clean_text(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "film_links": film_links,
        "film_links_count": len(film_links),
        "pagination_links": pagination_links,
        "forms": forms,
        "scripts": sorted(set(scripts)),
        "inline_discovery": inline_discovery[:30],
        "data_hints": data_hints[:80],
        "html_length": len(html_text or ""),
    }


def parse_sitemap_xml(xml_text: str) -> dict[str, Any]:
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    film_urls = [
        url
        for url in urls
        if urlparse(url).netloc.endswith("gosfilmofond.ru")
        and _FILM_DETAIL_RE.match(urlparse(url).path)
        and urlparse(url).path.rstrip("/") != "/films"
    ]
    nested_sitemaps = [url for url in urls if url.lower().endswith(".xml")]
    return {
        "url_count": len(urls),
        "film_url_count": len(film_urls),
        "film_url_samples": film_urls[:30],
        "nested_sitemaps": nested_sitemaps[:50],
    }


def summarize_rest_root(text: str) -> dict[str, Any]:
    try:
        payload = json.loads(text)
    except (TypeError, json.JSONDecodeError):
        return {
            "json": False,
            "routes_count": 0,
            "candidate_routes": [],
            "namespaces": [],
        }
    routes = payload.get("routes", {})
    if not isinstance(routes, dict):
        routes = {}
    candidates = [
        route
        for route in routes
        if re.search(r"film|movie|catalog|search|filter", route, re.I)
    ]
    namespaces = payload.get("namespaces", [])
    return {
        "json": True,
        "routes_count": len(routes),
        "candidate_routes": sorted(candidates)[:100],
        "namespaces": namespaces if isinstance(namespaces, list) else [],
    }


def _mechanism_candidates(
    catalog: dict[str, Any],
    sitemaps: list[dict[str, Any]],
    rest: dict[str, Any] | None,
) -> list[str]:
    mechanisms = []
    if catalog.get("film_links_count", 0):
        mechanisms.append("server_rendered_catalog_links")
    if catalog.get("pagination_links"):
        mechanisms.append("server_rendered_pagination")
    if any(
        item.get("parsed", {}).get("film_url_count", 0)
        for item in sitemaps
    ):
        mechanisms.append("sitemap_film_urls")
    if any(
        item.get("parsed", {}).get("nested_sitemaps")
        for item in sitemaps
    ):
        mechanisms.append("sitemap_index")
    if rest and rest.get("candidate_routes"):
        mechanisms.append("wordpress_rest_candidate_routes")
    if catalog.get("inline_discovery") or catalog.get("data_hints"):
        mechanisms.append("client_side_ajax_or_filter_hints")
    return mechanisms


def run_gosfilmofond_probe(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()
    target_urls = [
        GOSFILMOFOND_HOME_URL,
        GOSFILMOFOND_CATALOG_URL,
        GOSFILMOFOND_REST_ROOT,
        *GOSFILMOFOND_SITEMAP_CANDIDATES,
    ]
    robots = evaluate_robots(session, target_urls)
    allowed = _allowed_map(robots)

    result: dict[str, Any] = {
        "schema_version": "1.0.0",
        "probe_version": GOSFILMOFOND_PROBE_VERSION,
        "status": "completed",
        "automatic_incorporation_authorized": False,
        "brute_force_id_scan_performed": False,
        "experimental_model_used": False,
        "robots": robots,
        "home": None,
        "catalog": None,
        "sitemaps": [],
        "rest": None,
        "enumeration_mechanisms": [],
        "gate_assessment": "undetermined",
        "limitations": [
            "Probe inspects only public technical surfaces and openly exposed metadata.",
            "It does not assert completeness of physical holdings or public streaming availability.",
            "A production collector requires a separate admission decision after live evidence.",
        ],
    }

    if allowed.get(GOSFILMOFOND_HOME_URL, False):
        response = fetch_public_url(session, GOSFILMOFOND_HOME_URL)
        result["home"] = {
            "requested_url": response.requested_url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "content_type": response.content_type,
            "error": response.error,
            "html_length": len(response.text),
        }

    if allowed.get(GOSFILMOFOND_CATALOG_URL, False):
        response = fetch_public_url(session, GOSFILMOFOND_CATALOG_URL)
        catalog = {
            "requested_url": response.requested_url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "content_type": response.content_type,
            "error": response.error,
        }
        if response.status_code == 200 and not response.error:
            catalog.update(
                parse_catalog_html(
                    response.text,
                    response.final_url or GOSFILMOFOND_CATALOG_URL,
                )
            )
        result["catalog"] = catalog

    for sitemap_url in GOSFILMOFOND_SITEMAP_CANDIDATES:
        item = {
            "url": sitemap_url,
            "allowed": allowed.get(sitemap_url, False),
            "status_code": None,
            "error": None,
            "parsed": {
                "url_count": 0,
                "film_url_count": 0,
                "film_url_samples": [],
                "nested_sitemaps": [],
            },
        }
        if item["allowed"]:
            response = fetch_public_url(session, sitemap_url)
            item["status_code"] = response.status_code
            item["error"] = response.error
            if response.status_code == 200 and not response.error:
                item["parsed"] = parse_sitemap_xml(response.text)
        result["sitemaps"].append(item)

    if allowed.get(GOSFILMOFOND_REST_ROOT, False):
        response = fetch_public_url(session, GOSFILMOFOND_REST_ROOT)
        result["rest"] = {
            "requested_url": response.requested_url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "content_type": response.content_type,
            "error": response.error,
            **(
                summarize_rest_root(response.text)
                if response.status_code == 200 and not response.error
                else {
                    "json": False,
                    "routes_count": 0,
                    "candidate_routes": [],
                    "namespaces": [],
                }
            ),
        }

    catalog = result.get("catalog") or {}
    result["enumeration_mechanisms"] = _mechanism_candidates(
        catalog,
        result["sitemaps"],
        result.get("rest"),
    )

    catalog_ok = catalog.get("status_code") == 200 and not catalog.get("error")
    robots_catalog = allowed.get(GOSFILMOFOND_CATALOG_URL, False)
    mechanisms = result["enumeration_mechanisms"]
    if not robots_catalog:
        result["gate_assessment"] = "hold_robots_not_allowed_or_unverifiable"
    elif not catalog_ok:
        result["gate_assessment"] = "hold_catalog_unreachable"
    elif mechanisms:
        result["gate_assessment"] = "candidate_enumeration_mechanism_detected_requires_collector_validation"
    else:
        result["gate_assessment"] = "hold_no_reproducible_enumeration_mechanism_detected"

    return result


__all__ = [
    "GOSFILMOFOND_CATALOG_URL",
    "GOSFILMOFOND_HOME_URL",
    "GOSFILMOFOND_PROBE_VERSION",
    "GOSFILMOFOND_REST_ROOT",
    "GOSFILMOFOND_ROBOTS_URL",
    "GOSFILMOFOND_SITEMAP_CANDIDATES",
    "ProbeResponse",
    "evaluate_robots",
    "fetch_public_url",
    "parse_catalog_html",
    "parse_sitemap_xml",
    "robots_allowed_rfc9309",
    "run_gosfilmofond_probe",
    "summarize_rest_root",
]
