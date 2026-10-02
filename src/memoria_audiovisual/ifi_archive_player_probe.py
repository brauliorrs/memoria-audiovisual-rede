"""Technical discovery probe for the IFI Irish Film Archive Player.

This module does not collect or download audiovisual media. It inspects only
public HTML/metadata discovery surfaces to determine whether the IFI Archive
Player can later be enumerated reproducibly as a bounded metadata corpus.
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


IFI_PLAYER_HOME_URL = "https://ifiarchiveplayer.ie/"
IFI_PLAYER_BROWSE_URL = "https://ifiarchiveplayer.ie/browse/"
IFI_PLAYER_COLLECTIONS_URL = "https://ifiarchiveplayer.ie/collections/"
IFI_PLAYER_ROBOTS_URL = "https://ifiarchiveplayer.ie/robots.txt"
IFI_PLAYER_REST_ROOT = "https://ifiarchiveplayer.ie/wp-json/"
IFI_PLAYER_SITEMAP_CANDIDATES = (
    "https://ifiarchiveplayer.ie/wp-sitemap.xml",
    "https://ifiarchiveplayer.ie/sitemap_index.xml",
    "https://ifiarchiveplayer.ie/sitemap.xml",
)
IFI_PLAYER_PROBE_VERSION = "2026-10-ifi-archive-player-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_DISCOVERY_RE = re.compile(
    r"(?:browse|search|filter|category|collection|archive|page|pagination|"
    r"wp-json|rest|api|ajax|load[_-]?more)",
    re.I,
)
_SEARCH_RE = re.compile(r"(?:search|query|keyword|filter|s=|browse)", re.I)
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_EXCLUDED_ROOTS = {
    "",
    "about",
    "app",
    "browse",
    "collections",
    "contact",
    "donate",
    "legal",
    "privacy-policy",
    "terms-conditions",
    "cookie-information",
    "ifi-platforms",
    "virtual-exhibitions",
    "wp-admin",
    "wp-json",
    "feed",
}


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
            "Accept": (
                "text/html,application/xhtml+xml,application/json,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-IE,en;q=0.9",
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
    response = fetch_public_url(session, IFI_PLAYER_ROBOTS_URL)
    result: dict[str, Any] = {
        "robots_url": IFI_PLAYER_ROBOTS_URL,
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


def _allowed_map(result: dict[str, Any]) -> dict[str, bool]:
    return {
        item["url"]: bool(item["allowed"])
        for item in result.get("targets", [])
        if item.get("url")
    }


def _likely_film_permalink(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "ifiarchiveplayer.ie":
        return False
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 1:
        return False
    slug = parts[0].lower()
    if slug in _EXCLUDED_ROOTS:
        return False
    if slug.endswith(".xml"):
        return False
    if slug.startswith(("category", "tag", "author", "wp-")):
        return False
    return True


def parse_surface_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")

    forms = []
    search_forms = []
    for form in soup.find_all("form"):
        controls = []
        for node in form.find_all(["input", "select", "textarea", "button"]):
            name = _clean(node.get("name") or node.get("id"))
            value = _clean(node.get("value"), limit=200)
            placeholder = _clean(node.get("placeholder"), limit=200)
            label = _clean(node.get_text(" ", strip=True), limit=200)
            if name or value or placeholder or label:
                controls.append(
                    {
                        "name": name,
                        "type": _clean(node.get("type") or node.name),
                        "value": value,
                        "placeholder": placeholder,
                        "label": label,
                    }
                )
        row = {
            "action": urljoin(page_url, form.get("action") or page_url),
            "method": _clean(form.get("method") or "get").lower(),
            "controls": controls[:100],
        }
        forms.append(row)
        marker = " ".join(
            [
                row["action"],
                " ".join(
                    " ".join(str(control.get(key, "")) for key in (
                        "name", "value", "placeholder", "label"
                    ))
                    for control in controls
                ),
            ]
        )
        if _SEARCH_RE.search(marker):
            search_forms.append(row)

    film_links = []
    discovery_links = []
    pagination_links = []
    seen_films: set[str] = set()
    seen_discovery: set[str] = set()
    seen_pagination: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        text = _clean(anchor.get_text(" ", strip=True), limit=250)
        if _likely_film_permalink(absolute) and absolute not in seen_films:
            seen_films.add(absolute)
            film_links.append({"url": absolute, "text": text})
        marker = f"{absolute} {text}"
        if _DISCOVERY_RE.search(marker) and absolute not in seen_discovery:
            seen_discovery.add(absolute)
            discovery_links.append({"url": absolute, "text": text})
        classes = " ".join(anchor.get("class", []))
        rel = " ".join(anchor.get("rel", []))
        if re.search(r"(?:next|prev|page|pagination)", f"{classes} {rel} {text}", re.I):
            if absolute not in seen_pagination:
                seen_pagination.add(absolute)
                pagination_links.append(absolute)

    scripts = []
    inline_hints = []
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            scripts.append(urljoin(page_url, src))
        inline = script.string or script.get_text(" ", strip=True)
        if inline and _DISCOVERY_RE.search(inline):
            inline_hints.append(_clean(inline, limit=1200))

    return {
        "title": _clean(
            soup.title.get_text(" ", strip=True) if soup.title else ""
        ),
        "forms": forms,
        "search_forms": search_forms,
        "film_links": film_links[:200],
        "film_links_count": len(film_links),
        "discovery_links": discovery_links[:100],
        "pagination_links": pagination_links[:50],
        "scripts": sorted(set(scripts)),
        "inline_hints": inline_hints[:30],
        "html_length": len(html_text or ""),
    }


def parse_sitemap(xml_text: str) -> dict[str, Any]:
    urls = [_clean(item) for item in _XML_LOC_RE.findall(xml_text or "")]
    film_candidates = [url for url in urls if _likely_film_permalink(url)]
    nested = [url for url in urls if url.lower().endswith(".xml")]
    return {
        "url_count": len(urls),
        "film_candidate_count": len(film_candidates),
        "film_candidate_samples": film_candidates[:50],
        "nested_sitemaps": nested[:50],
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

    routes = payload.get("routes", {}) if isinstance(payload, dict) else {}
    namespaces = payload.get("namespaces", []) if isinstance(payload, dict) else []
    candidates = [
        route
        for route in routes
        if re.search(r"(?:archive|film|video|search|post|collection)", route, re.I)
    ]
    return {
        "json": True,
        "routes_count": len(routes),
        "candidate_routes": candidates[:100],
        "namespaces": namespaces[:50] if isinstance(namespaces, list) else [],
    }


_POST_SITEMAP_PATH_RE = re.compile(r"^/post-sitemap(?:\d+)?\.xml$", re.I)
_FILM_LABEL_RE = re.compile(
    r"(?:Category|Directed by|Produced by|Year|Duration|Language)\s*:",
    re.I,
)


def _film_detail_semantics(html_text: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    labels = sorted(set(match.group(0).rstrip(":") for match in _FILM_LABEL_RE.finditer(text)))
    return {
        "labels": labels,
        "label_count": len(labels),
        "film_semantics_confirmed": len(labels) >= 2,
        "title": _clean(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else ""),
    }


def probe_bounded_post_sitemaps(
    session: requests.Session,
    *,
    robots_text: str,
    sitemaps: list[dict[str, Any]],
) -> dict[str, Any]:
    discovered = []
    for item in sitemaps:
        for url in (item.get("parsed") or {}).get("nested_sitemaps", []):
            parsed = urlparse(url)
            if (
                parsed.netloc.lower() == "ifiarchiveplayer.ie"
                and _POST_SITEMAP_PATH_RE.match(parsed.path)
            ):
                discovered.append(url)
    post_sitemaps = sorted(set(discovered))
    selected = post_sitemaps[:2]

    partitions = []
    all_sets = []
    detail_samples = []
    for url in selected:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, url):
            partitions.append(
                {"url": url, "status": "blocked_by_robots", "film_candidate_count": 0}
            )
            all_sets.append(set())
            continue
        response = fetch_public_url(session, url)
        parsed = (
            parse_sitemap(response.text)
            if response.status_code == 200 and not response.error
            else {
                "url_count": 0,
                "film_candidate_count": 0,
                "film_candidate_samples": [],
                "nested_sitemaps": [],
            }
        )
        candidates = [
            item
            for item in _XML_LOC_RE.findall(response.text or "")
            if _likely_film_permalink(_clean(item))
        ]
        candidate_set = set(candidates)
        all_sets.append(candidate_set)
        partitions.append(
            {
                "url": url,
                "status_code": response.status_code,
                "error": response.error,
                "url_count": parsed["url_count"],
                "film_candidate_count": len(candidate_set),
                "film_candidate_samples": sorted(candidate_set)[:20],
            }
        )
        if candidates:
            detail_url = sorted(candidate_set)[0]
            if robots_allowed(robots_text, CRAWLER_TOKEN, detail_url):
                detail_response = fetch_public_url(session, detail_url)
                semantics = (
                    _film_detail_semantics(detail_response.text)
                    if detail_response.status_code == 200 and not detail_response.error
                    else {
                        "labels": [],
                        "label_count": 0,
                        "film_semantics_confirmed": False,
                        "title": "",
                    }
                )
                detail_samples.append(
                    {
                        "url": detail_url,
                        "status_code": detail_response.status_code,
                        "error": detail_response.error,
                        **semantics,
                    }
                )

    disjoint = (
        len(all_sets) == 2
        and bool(all_sets[0])
        and bool(all_sets[1])
        and all_sets[0].isdisjoint(all_sets[1])
    )
    unique_urls = set().union(*all_sets) if all_sets else set()
    partitions_ok = (
        len(partitions) == 2
        and all(row.get("status_code") == 200 and not row.get("error") for row in partitions)
        and all(row.get("film_candidate_count", 0) > 0 for row in partitions)
    )
    detail_semantics_ok = (
        len(detail_samples) == 2
        and all(row.get("film_semantics_confirmed") for row in detail_samples)
    )
    return {
        "post_sitemaps_discovered": post_sitemaps,
        "partitions_selected": selected,
        "all_discovered_post_sitemaps_covered": (
            bool(post_sitemaps) and len(selected) == len(post_sitemaps)
        ),
        "partitions": partitions,
        "unique_film_permalink_candidates": len(unique_urls),
        "disjoint_partitions": disjoint,
        "detail_samples": detail_samples,
        "reproducible_bounded_enumeration": (
            partitions_ok and disjoint and detail_semantics_ok
        ),
    }



def run_ifi_archive_player_probe(
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()
    targets = (
        IFI_PLAYER_HOME_URL,
        IFI_PLAYER_BROWSE_URL,
        IFI_PLAYER_COLLECTIONS_URL,
        IFI_PLAYER_REST_ROOT,
        *IFI_PLAYER_SITEMAP_CANDIDATES,
    )
    robots, robots_text = evaluate_robots(session, targets)
    allowed = _allowed_map(robots)

    surfaces = []
    for kind, url in (
        ("home", IFI_PLAYER_HOME_URL),
        ("browse", IFI_PLAYER_BROWSE_URL),
        ("collections", IFI_PLAYER_COLLECTIONS_URL),
    ):
        if not allowed.get(url, False):
            surfaces.append(
                {"kind": kind, "url": url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(session, url)
        parsed = (
            parse_surface_html(response.text, response.final_url or url)
            if response.status_code == 200 and not response.error
            else None
        )
        surfaces.append(
            {
                "kind": kind,
                "url": url,
                "final_url": response.final_url,
                "status_code": response.status_code,
                "content_type": response.content_type,
                "error": response.error,
                "parsed": parsed,
            }
        )

    sitemaps = []
    for url in IFI_PLAYER_SITEMAP_CANDIDATES:
        if not allowed.get(url, False):
            sitemaps.append({"url": url, "status": "blocked_by_robots"})
            continue
        response = fetch_public_url(session, url)
        sitemaps.append(
            {
                "url": url,
                "status_code": response.status_code,
                "content_type": response.content_type,
                "error": response.error,
                "parsed": (
                    parse_sitemap(response.text)
                    if response.status_code == 200 and not response.error
                    else None
                ),
            }
        )

    rest = None
    if allowed.get(IFI_PLAYER_REST_ROOT, False):
        response = fetch_public_url(session, IFI_PLAYER_REST_ROOT)
        rest = {
            "url": IFI_PLAYER_REST_ROOT,
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

    browse = next(
        (row for row in surfaces if row.get("kind") == "browse"),
        {},
    )
    parsed_browse = browse.get("parsed") or {}
    film_links = parsed_browse.get("film_links", [])
    search_forms = parsed_browse.get("search_forms", [])
    pagination_links = parsed_browse.get("pagination_links", [])

    mechanisms = []
    if film_links:
        mechanisms.append("browse_public_film_permalink_candidates")
    if search_forms:
        mechanisms.append("browse_public_search_form")
    if pagination_links:
        mechanisms.append("browse_pagination_links")
    if any(
        (item.get("parsed") or {}).get("film_candidate_count", 0)
        for item in sitemaps
    ):
        mechanisms.append("sitemap_film_permalink_candidates")
    if rest and rest.get("candidate_routes"):
        mechanisms.append("wordpress_rest_candidate_routes")

    bounded = probe_bounded_post_sitemaps(
        session,
        robots_text=robots_text,
        sitemaps=sitemaps,
    )

    browse_allowed = allowed.get(IFI_PLAYER_BROWSE_URL, False)
    if not browse_allowed:
        gate = "hold_robots_not_allowed_or_unverifiable"
    elif bounded["reproducible_bounded_enumeration"]:
        gate = "bounded_post_sitemap_enumeration_validated_for_collector_engineering"
    elif film_links and (
        search_forms
        or pagination_links
        or bounded["post_sitemaps_discovered"]
        or "wordpress_rest_candidate_routes" in mechanisms
    ):
        gate = "public_enumeration_candidate_detected_bounded_probe_required"
    else:
        gate = "hold_no_reproducible_enumeration_candidate_detected"

    return {
        "probe_version": IFI_PLAYER_PROBE_VERSION,
        "institution": "IFI Irish Film Archive",
        "queue_code": "fiaf-ifi-irish-film-archive",
        "surface": "IFI Archive Player",
        "automatic_incorporation_authorized": False,
        "brute_force_id_scan_performed": False,
        "media_download_performed": False,
        "experimental_model_used": False,
        "public_platform_count_context_only": "over_1000_films",
        "robots": robots,
        "robots_policy_retained_in_memory_only": bool(robots_text),
        "surfaces": surfaces,
        "sitemaps": sitemaps,
        "rest": rest,
        "bounded_post_sitemap_probe": bounded,
        "enumeration_mechanisms": mechanisms,
        "gate_assessment": gate,
        "next_action": (
            "engineer_staged_collector_from_post_sitemaps"
            if gate
            == "bounded_post_sitemap_enumeration_validated_for_collector_engineering"
            else (
                "engineer_bounded_two_page_or_partition_probe"
                if gate
                == "public_enumeration_candidate_detected_bounded_probe_required"
                else "protocol_hold_or_retest"
            )
        ),
    }


__all__ = [
    "IFI_PLAYER_BROWSE_URL",
    "IFI_PLAYER_COLLECTIONS_URL",
    "IFI_PLAYER_HOME_URL",
    "IFI_PLAYER_REST_ROOT",
    "IFI_PLAYER_ROBOTS_URL",
    "parse_sitemap",
    "parse_surface_html",
    "probe_bounded_post_sitemaps",
    "robots_allowed",
    "run_ifi_archive_player_probe",
]
