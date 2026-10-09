"""Fail-closed public-surface probe for the Jean Vigo Institute."""
from __future__ import annotations

import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT

JEAN_VIGO_HOME_URL = "https://www.inst-jeanvigo.eu/"
JEAN_VIGO_ROBOTS_URL = "https://www.inst-jeanvigo.eu/robots.txt"
JEAN_VIGO_COLLECTIONS_URL = (
    "https://www.inst-jeanvigo.eu/"
    "collections-cinematheque-perpignan-institut-jean-vigo"
)
JEAN_VIGO_FILMS_URL = JEAN_VIGO_COLLECTIONS_URL + "/les-films"
JEAN_VIGO_AMATEUR_FILMS_URL = (
    JEAN_VIGO_COLLECTIONS_URL
    + "/memoire-filmique-du-sud-pyrenees-mediterranee-films-amateurs"
)
JEAN_VIGO_PROBE_VERSION = "2026-10-jean-vigo-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_ALLOWED_HOST = "www.inst-jeanvigo.eu"
_SITEMAP_DIRECTIVE_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_ASSET_SUFFIXES = (
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".css", ".js",
    ".ico", ".pdf", ".zip", ".mp3", ".mp4", ".mov", ".avi",
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
            "User-Agent": (
                f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-probe)"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "*/*;q=0.8"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
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
    explicit: list[tuple[int, dict[str, Any]]] = []
    for group in groups:
        matches = [
            len(token)
            for token in group["agents"]
            if token and token != "*" and token in agent
        ]
        if matches:
            explicit.append((max(matches), group))
    if explicit:
        longest = max(length for length, _ in explicit)
        selected = [group for length, group in explicit if length == longest]
    else:
        selected = [group for group in groups if "*" in group["agents"]]
    if not selected:
        return True

    parsed = urlparse(url)
    target = parsed.path or "/"
    if parsed.query:
        target += "?" + parsed.query

    rules: list[tuple[int, bool]] = []
    for group in selected:
        for allowance, pattern in group["rules"]:
            if _rule_regex(pattern).search(target):
                score = len(pattern.rstrip("$").replace("*", ""))
                rules.append((score, allowance))
    if not rules:
        return True
    longest = max(score for score, _ in rules)
    return any(allowed for score, allowed in rules if score == longest)


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
                requested_url,
                current_url,
                getattr(response, "status_code", None),
                "",
                "",
                "redirect_target_outside_authorized_origin",
            )
        if robots_text is not None and not robots_allowed(
            robots_text, CRAWLER_TOKEN, current_url
        ):
            return ProbeResponse(
                requested_url,
                current_url,
                getattr(response, "status_code", None),
                "",
                "",
                "target_blocked_by_robots",
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
                requested_url,
                current_url,
                getattr(response, "status_code", None),
                "",
                "",
                f"{type(exc).__name__}: {exc}",
            )
        if response.status_code in {301, 302, 303, 307, 308}:
            location = response.headers.get("location", "")
            if not location:
                return ProbeResponse(
                    requested_url,
                    current_url,
                    response.status_code,
                    response.headers.get("content-type", ""),
                    "",
                    "redirect_without_location",
                )
            current_url = urljoin(current_url, location)
            continue
        return ProbeResponse(
            requested_url,
            current_url,
            response.status_code,
            response.headers.get("content-type", ""),
            response.text,
            None,
        )
    return ProbeResponse(
        requested_url,
        current_url,
        getattr(response, "status_code", None),
        "",
        "",
        "redirect_limit_exceeded",
    )


def parse_surface_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    same_host: list[str] = []
    external: list[str] = []
    forms: list[dict[str, Any]] = []
    scripts: list[str] = []
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc.lower() == _ALLOWED_HOST:
            if absolute not in same_host:
                same_host.append(absolute)
        elif absolute not in external:
            external.append(absolute)
    for form in soup.find_all("form"):
        action = urljoin(page_url, form.get("action", ""))
        forms.append(
            {
                "method": str(form.get("method", "get")).upper(),
                "action": action,
                "input_names": sorted(
                    {
                        str(node.get("name", "")).strip()
                        for node in form.find_all(
                            ["input", "select", "textarea"]
                        )
                        if str(node.get("name", "")).strip()
                    }
                )[:50],
            }
        )
    for script in soup.find_all("script", src=True):
        absolute = urljoin(page_url, script.get("src", ""))
        if urlparse(absolute).netloc.lower() == _ALLOWED_HOST:
            scripts.append(absolute)

    visible = _clean(soup.get_text(" ", strip=True), limit=12000)
    lowered = visible.lower()
    return {
        "title": _clean(soup.title.get_text(" ", strip=True) if soup.title else ""),
        "same_host_links": same_host[:250],
        "external_links": external[:250],
        "forms": forms[:20],
        "script_urls": sorted(set(scripts))[:80],
        "mentions_cineressources": "ciné-ressources" in lowered
        or "cine-ressources" in lowered,
        "mentions_memoire_filmique": "mémoire filmique" in lowered
        or "memoire filmique" in lowered,
        "mentions_online": "en ligne" in lowered,
        "html_length": len(html_text or ""),
    }


def _local_tag(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def parse_sitemap(xml_text: str) -> dict[str, Any]:
    same_host_pages: list[str] = []
    nested: list[str] = []
    rejected: list[str] = []
    urls: list[str] = []

    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError:
        # Keep evidence about malformed payloads without guessing sitemap roles.
        urls = [_clean(value) for value in _XML_LOC_RE.findall(xml_text or "")]
        return {
            "url_count": len(urls),
            "same_host_page_count": 0,
            "same_host_pages": [],
            "nested_sitemaps": [],
            "rejected_urls": [],
            "parse_error": True,
        }

    root_kind = _local_tag(root.tag)
    for container in list(root):
        container_kind = _local_tag(container.tag)
        loc_value = ""
        for child in list(container):
            if _local_tag(child.tag) == "loc":
                loc_value = _clean(child.text)
                break
        if not loc_value:
            continue
        urls.append(loc_value)
        parsed = urlparse(loc_value)
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != _ALLOWED_HOST:
            rejected.append(loc_value)
            continue

        is_nested = root_kind == "sitemapindex" and container_kind == "sitemap"
        if is_nested:
            nested.append(loc_value)
            continue
        if parsed.path.lower().endswith(_ASSET_SUFFIXES):
            continue
        same_host_pages.append(loc_value)

    return {
        "url_count": len(urls),
        "same_host_page_count": len(set(same_host_pages)),
        "same_host_pages": sorted(set(same_host_pages)),
        "nested_sitemaps": sorted(set(nested)),
        "rejected_urls": sorted(set(rejected)),
        "parse_error": False,
    }


def classify_public_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.startswith("/agenda/"):
        return "agenda_or_programming"
    if "collections-cinematheque" in path or "memoire-filmique" in path:
        return "institutional_collection_page"
    if "/actualites/" in path or "/mots-cles/" in path or "/categories/" in path:
        return "editorial_page"
    return "other_public_page"


def _evaluate_robots(session: requests.Session) -> tuple[dict[str, Any], str]:
    response = fetch_public_url(session, JEAN_VIGO_ROBOTS_URL)
    result: dict[str, Any] = {
        "url": JEAN_VIGO_ROBOTS_URL,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
        "sitemaps": [],
        "excerpt": _clean(response.text, limit=2500),
    }
    if response.error:
        result["mode"] = "unverifiable"
        return result, ""
    if response.status_code in {404, 410}:
        result["mode"] = "absent"
        return result, ""
    if response.status_code != 200:
        result["mode"] = "unverifiable"
        return result, ""
    text = response.text or ""
    if not text.strip() or "<html" in text.lower():
        result["mode"] = "unverifiable"
        return result, ""
    result["mode"] = "evaluated_rfc9309"
    result["sitemaps"] = sorted(set(_SITEMAP_DIRECTIVE_RE.findall(text)))
    return result, text


def _fetch_declared_sitemaps(
    session: requests.Session,
    sitemap_urls: list[str],
    robots_text: str,
    *,
    max_sitemaps: int = 20,
) -> tuple[list[dict[str, Any]], list[str], bool]:
    queue = list(sitemap_urls)
    seen: set[str] = set()
    reports: list[dict[str, Any]] = []
    pages: list[str] = []
    truncated = False
    while queue:
        if len(seen) >= max_sitemaps:
            truncated = True
            break
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != _ALLOWED_HOST:
            reports.append({"url": url, "status": "rejected_origin"})
            continue
        response = fetch_public_url(session, url, robots_text=robots_text)
        report: dict[str, Any] = {
            "url": url,
            "status_code": response.status_code,
            "error": response.error,
        }
        if response.error or response.status_code != 200:
            report["status"] = "fetch_failed"
            reports.append(report)
            continue
        parsed_map = parse_sitemap(response.text)
        report.update(parsed_map)
        report["status"] = "ok"
        reports.append(report)
        pages.extend(parsed_map["same_host_pages"])
        for child in parsed_map["nested_sitemaps"]:
            if child not in seen and child not in queue:
                queue.append(child)
    return reports, sorted(set(pages)), truncated


def run_jean_vigo_probe(session: requests.Session | None = None) -> dict[str, Any]:
    session = session or _session()
    robots, robots_text = _evaluate_robots(session)
    payload: dict[str, Any] = {
        "probe_version": JEAN_VIGO_PROBE_VERSION,
        "institution": "Jean Vigo Institute",
        "source_family": "INEDITS",
        "robots": robots,
        "surfaces": [],
        "sitemaps": [],
        "sitemap_pages_total": 0,
        "sitemap_traversal_truncated": False,
        "classification_counts": {},
        "external_archive_hints": [],
        "gate_assessment": "hold_unverified_public_enumeration",
        "next_action": "record_hold_and_continue_queue",
    }
    if robots["mode"] == "unverifiable":
        payload["gate_assessment"] = "hold_robots_unverifiable"
        return payload

    surface_urls = (
        JEAN_VIGO_HOME_URL,
        JEAN_VIGO_COLLECTIONS_URL,
        JEAN_VIGO_FILMS_URL,
        JEAN_VIGO_AMATEUR_FILMS_URL,
    )
    external_hints: set[str] = set()
    for url in surface_urls:
        if robots_text and not robots_allowed(robots_text, CRAWLER_TOKEN, url):
            payload["surfaces"].append(
                {"url": url, "status": "blocked_by_robots"}
            )
            continue
        response = fetch_public_url(
            session,
            url,
            robots_text=robots_text if robots_text else None,
        )
        row: dict[str, Any] = {
            "url": url,
            "status_code": response.status_code,
            "error": response.error,
        }
        if not response.error and response.status_code == 200:
            parsed = parse_surface_html(response.text, response.final_url or url)
            row.update(parsed)
            row["status"] = "ok"
            for link in parsed["external_links"]:
                host = urlparse(link).netloc.lower()
                if (
                    "memoirefilmiquedusud" in host
                    or "purl.org" in host
                    or "cine-ressources" in link.lower()
                ):
                    external_hints.add(link)
        else:
            row["status"] = "fetch_failed"
        payload["surfaces"].append(row)

    if robots["sitemaps"]:
        reports, pages, truncated = _fetch_declared_sitemaps(
            session,
            robots["sitemaps"],
            robots_text,
        )
        payload["sitemaps"] = reports
        payload["sitemap_pages_total"] = len(pages)
        payload["sitemap_traversal_truncated"] = truncated
        counts: dict[str, int] = {}
        for page in pages:
            key = classify_public_url(page)
            counts[key] = counts.get(key, 0) + 1
        payload["classification_counts"] = counts

    payload["external_archive_hints"] = sorted(external_hints)
    collection_pages = payload["classification_counts"].get(
        "institutional_collection_page", 0
    )
    if collection_pages and not payload["sitemap_traversal_truncated"]:
        payload["gate_assessment"] = (
            "investigate_sitemap_collection_pages_semantics_before_staged"
        )
        payload["next_action"] = (
            "sample_sitemap_collection_pages_and_test_record_enumeration"
        )
    elif external_hints:
        payload["gate_assessment"] = "hold_primary_site_points_to_external_archive"
        payload["next_action"] = (
            "protocol_primary_site_and_assess_external_archive_as_separate_surface"
        )
    return payload


def dumps_probe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
