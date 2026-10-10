"""Robots-first, fail-closed public discovery for Jugoslovenska Kinoteka (#81)."""
from __future__ import annotations

import gzip
import hashlib
import io
import json
import re
import time
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT
from .jean_vigo_probe import robots_allowed

VERSION = "2026-10-jugoslovenska-kinoteka-probe-v1"
USER_AGENT = "MemoriaAudiovisualRede"
HOME = "https://www.kinoteka.org.rs/"
ROOT_HOST = "www.kinoteka.org.rs"
HOSTS = frozenset({"www.kinoteka.org.rs", "kinoteka.org.rs", "en.kinoteka.org.rs"})
SURFACES = (
    ("homepage", HOME),
    ("film_archive", "https://www.kinoteka.org.rs/arhiv-jugoslovenske-kinoteke/"),
    ("institution", "https://www.kinoteka.org.rs/jugoslovenska-kinoteka/"),
    ("heritage_100", "https://www.kinoteka.org.rs/srpski-igrani-filmovi-1911-1999-100-najboljih/"),
    ("english_archive", "https://en.kinoteka.org.rs/archive/"),
)
SITEMAP_RE = re.compile(r"(?im)^\s*sitemap:\s*(\S+)\s*$")
MAX_XML_BYTES = 8 * 1024 * 1024
MAX_SITEMAPS = 30
MAX_LOC_URLS = 50000
REDIRECT_LIMIT = 5


def _host(url: str, *, allow_http: bool = False) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme not in ({"https", "http"} if allow_http else {"https"}):
        return None
    try:
        if parsed.port not in (None, 443 if parsed.scheme == "https" else 80):
            return None
    except ValueError:
        return None
    if parsed.username or parsed.password or parsed.fragment:
        return None
    return parsed.hostname if parsed.hostname in HOSTS else None


def _headers() -> dict[str, str]:
    return {
        **HEADERS,
        "User-Agent": f"{USER_AGENT}/1.0 (+public-heritage-metadata-probe)",
        "Accept": "text/html,application/xml,text/xml,*/*;q=0.5",
    }


@dataclass(frozen=True)
class Response:
    url: str
    final_url: str | None
    status: int | None
    text: str
    body: bytes
    content_type: str
    error: str | None


class RobotsGuard:
    """Each HTTPS host has its own robots policy; never assume sibling permission."""

    def __init__(self, session: requests.Session):
        self.session = session
        self.rules: dict[str, str] = {}
        self.evidence: dict[str, dict[str, Any]] = {}

    def allowed(self, url: str) -> bool:
        host = _host(url)
        if not host:
            return False
        if host not in self.evidence:
            self.check_host(host)
        row = self.evidence[host]
        if row["mode"] == "unverifiable":
            return False
        if row["mode"] == "absent":
            return True
        return robots_allowed(self.rules[host], USER_AGENT, url)

    def check_host(self, host: str) -> dict[str, Any]:
        if host in self.evidence:
            return self.evidence[host]
        url = f"https://{host}/robots.txt"
        row: dict[str, Any] = {
            "url": url, "mode": "unverifiable", "status_code": None,
            "error": None, "sitemaps": [],
        }
        # Create the row before any network operation; failures stay closed.
        self.evidence[host] = row
        try:
            response = self.session.get(
                url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=False,
            )
        except requests.RequestException as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            return row
        row["status_code"] = response.status_code
        if response.status_code in {301, 302, 303, 307, 308}:
            # Different origin (including www/apex) needs its own robots gate.
            location = urljoin(url, response.headers.get("location", ""))
            if _host(location) != host or urlparse(location).path != "/robots.txt":
                row["error"] = "robots_redirect_not_same_host"
                return row
            try:
                response = self.session.get(
                    location, timeout=(8, REQUEST_TIMEOUT),
                    allow_redirects=False,
                )
            except requests.RequestException as exc:
                row["error"] = f"{type(exc).__name__}: {exc}"
                return row
            row["status_code"] = response.status_code
        if response.status_code in {404, 410}:
            row["mode"] = "absent"
            return row
        if response.status_code != 200:
            row["error"] = "robots_not_200_or_absent"
            return row
        robots = response.text or ""
        if not robots.strip() or "<html" in robots.lower():
            row["error"] = "invalid_robots_document"
            return row
        row["mode"] = "evaluated"
        row["sitemaps"] = sorted(set(SITEMAP_RE.findall(robots)))
        self.rules[host] = robots
        return row

    def fetch(self, url: str) -> Response:
        original = url
        for _ in range(REDIRECT_LIMIT + 1):
            if not self.allowed(url):
                return Response(original, url, None, "", b"", "", "origin_or_robots_block")
            try:
                response = self.session.get(
                    url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=False,
                )
            except requests.RequestException as exc:
                return Response(original, url, None, "", b"", "",
                                f"{type(exc).__name__}: {exc}")
            if response.status_code in {301, 302, 303, 307, 308}:
                location = response.headers.get("location", "")
                if not location:
                    return Response(original, url, response.status_code, "", b"",
                                    "", "redirect_without_location")
                target = urljoin(url, location)
                if not _host(target):
                    return Response(original, target, response.status_code, "",
                                    b"", "", "redirect_outside_https_host_scope")
                url = target
                continue
            body = getattr(response, "content", b"") or b""
            return Response(
                original, url, response.status_code, response.text or "",
                body, response.headers.get("content-type", ""), None,
            )
        return Response(original, url, None, "", b"", "", "redirect_limit_exceeded")

    def resolve_declared_sitemap(self, url: str) -> tuple[str | None, str]:
        host = _host(url, allow_http=True)
        if not host:
            return None, "rejected_origin"
        if urlparse(url).scheme == "https":
            return url, "https_declared"
        # HTTP is permitted ONLY to inspect a redirect to authorized HTTPS.
        try:
            response = self.session.get(
                url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=False,
            )
        except requests.RequestException:
            return None, "http_redirect_unverifiable"
        if response.status_code not in {301, 302, 303, 307, 308}:
            return None, "http_content_not_accepted"
        target = urljoin(url, response.headers.get("location", ""))
        if not _host(target):
            return None, "http_redirect_outside_https_scope"
        # The target host's robots gate is checked by fetch() before its body.
        return target, "http_redirect_to_https"


def _xml_text(response: Response) -> str:
    raw = response.body or response.text.encode("utf-8")
    if raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
            raw = stream.read(MAX_XML_BYTES + 1)
    if len(raw) > MAX_XML_BYTES:
        raise ValueError("sitemap_decompressed_size_limit")
    return raw.decode("utf-8-sig")


def _local(tag: str) -> str:
    return str(tag).rsplit("}", 1)[-1].rsplit(":", 1)[-1].lower()


def parse_sitemap(text: str) -> tuple[str, list[str]]:
    """Roles come only from XML structure; malformed/mixed entries fail closed."""
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError("sitemap_invalid_xml") from exc
    kind = _local(root.tag)
    if kind not in {"sitemapindex", "urlset"}:
        raise ValueError("sitemap_invalid_root")
    container = "sitemap" if kind == "sitemapindex" else "url"
    values: list[str] = []
    for child in root:
        if _local(child.tag) != container:
            raise ValueError("sitemap_unexpected_container")
        loc = [node for node in child if _local(node.tag) == "loc"]
        if len(loc) != 1 or not (loc[0].text or "").strip():
            raise ValueError("sitemap_missing_or_duplicate_loc")
        values.append((loc[0].text or "").strip())
    # A WordPress sitemap may embed image/video/news extension elements,
    # including image:loc. Only loc in the root sitemap namespace identifies
    # a page or nested sitemap. Extension locs are not omitted records.
    namespace = (
        root.tag.split("}", 1)[0] + "}" if root.tag.startswith("{") else ""
    )
    sitemap_loc_tag = namespace + "loc"
    if len(values) != sum(
        1 for node in root.iter() if node.tag == sitemap_loc_tag
    ):
        raise ValueError("sitemap_unattributed_loc")
    if len(values) != len(set(values)):
        raise ValueError("sitemap_duplicate_loc")
    return kind, values


def parse_surface(html: str, base: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    forms: list[dict[str, Any]] = []
    links: set[str] = set()
    external: set[str] = set()
    sitemap_hints: set[str] = set()
    for tag in soup.select("a[href]"):
        url = urljoin(base, tag["href"])
        if _host(url):
            links.add(url)
        elif urlparse(url).scheme in {"http", "https"}:
            external.add(url)
    for tag in soup.select("link[rel][href]"):
        rels = [str(item).lower() for item in tag.get("rel", [])]
        if "sitemap" in rels:
            sitemap_hints.add(urljoin(base, tag["href"]))
    for form in soup.select("form"):
        forms.append({
            "action": urljoin(base, form.get("action") or ""),
            "method": str(form.get("method") or "GET").upper(),
            "inputs": sorted({
                tag.get("name", "") for tag in form.select("[name]")
                if tag.get("name")
            })[:30],
        })
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else (
        soup.title.get_text(" ", strip=True) if soup.title else ""
    )
    return {
        "title": title[:250],
        "same_host_links_sample": sorted(links)[:30],
        "same_host_link_count": len(links),
        "external_links_sample": sorted(external)[:20],
        "forms": forms[:10],
        "sitemap_hints": sorted(sitemap_hints),
        "html_size": len(html),
    }


def classify_page(url: str) -> str:
    path = urlparse(url).path.lower().strip("/")
    if path == "srpski-igrani-filmovi-1911-1999-100-najboljih":
        return "heritage_designation_100_list"
    if path.startswith(("repertoar", "program", "repertoire", "uzun-mirkova",
                        "kosovska", "mese", "fest")):
        return "screening_or_programming"
    if path.startswith(("vesti", "news", "aktuelno", "casopis", "magazine",
                        "category", "tag", "author", "page")):
        return "editorial_or_pagination"
    if path in {"jugoslovenska-kinoteka", "arhiv-jugoslovenske-kinoteke",
                "archive", "about", "biblioteka", "kontakt"}:
        return "institutional_overview"
    if any(item in path for item in ("katalog", "catalog", "filmograf",
                                     "filmska-grada", "film-archive")):
        return "possible_catalogue_surface"
    return "unverified_public_page"


def _sample(values: list[str], count: int = 12) -> list[str]:
    if not values:
        return []
    indexes = {int(i * (len(values) - 1) / max(1, count - 1))
               for i in range(min(len(values), count))}
    return [values[i] for i in sorted(indexes)]


def run_probe(session: requests.Session | None = None) -> dict[str, Any]:
    if session is None:
        session = requests.Session()
        session.headers.update(_headers())
    guard = RobotsGuard(session)
    primary = guard.check_host(ROOT_HOST)
    payload: dict[str, Any] = {
        "probe_version": VERSION, "institution": "Jugoslovenska Kinoteka",
        "analysis_number": 81, "robots": guard.evidence, "surfaces": [],
        "sitemap_reports": [], "enumerated_public_url_count": 0,
        "enumerated_url_sha256": None, "classification_counts": {},
        "candidate_url_sample": [], "traversal_complete": False,
        "gate_assessment": "hold_robots_unverifiable",
        "staged_collector_authorized": False,
        "notes": ["No media downloaded; no guessed IDs or private routes"],
    }
    if primary["mode"] == "unverifiable":
        return payload

    hints: set[str] = set()
    for name, url in SURFACES:
        response = guard.fetch(url)
        row: dict[str, Any] = {
            "name": name, "requested_url": url, "final_url": response.final_url,
            "status": response.status, "error": response.error,
        }
        if not response.error and response.status == 200 and "html" in response.content_type.lower():
            parsed = parse_surface(response.text, response.final_url or url)
            row.update(parsed)
            hints.update(parsed["sitemap_hints"])
        payload["surfaces"].append(row)

    initial = set()
    # Only publicly declared/discovered sitemaps, never guessed filenames.
    for policy in guard.evidence.values():
        initial.update(policy.get("sitemaps", []))
    initial.update(hints)
    queue: list[str] = []
    errors: list[str] = []
    for url in sorted(initial):
        resolved, transport = guard.resolve_declared_sitemap(url)
        payload["sitemap_reports"].append({
            "declared_url": url, "transport": transport,
        })
        if resolved and resolved not in queue:
            queue.append(resolved)
        if not resolved:
            errors.append("sitemap_declared_transport_unverifiable")
    seen: set[str] = set()
    enumerated: set[str] = set()
    while queue and len(seen) < MAX_SITEMAPS and len(enumerated) < MAX_LOC_URLS:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        response = guard.fetch(url)
        report: dict[str, Any] = {
            "url": url, "final_url": response.final_url,
            "status": response.status, "error": response.error,
        }
        if response.error or response.status != 200:
            report["result"] = "fetch_failed"
            errors.append("sitemap_fetch_failed")
            payload["sitemap_reports"].append(report)
            continue
        try:
            kind, locs = parse_sitemap(_xml_text(response))
        except (ValueError, OSError, UnicodeError, EOFError) as exc:
            report["result"] = f"parse_failed:{type(exc).__name__}"
            report["parse_error_code"] = str(exc)[:180]
            errors.append("sitemap_parse_failed")
            payload["sitemap_reports"].append(report)
            continue
        report.update({"result": "ok", "kind": kind, "loc_count": len(locs)})
        payload["sitemap_reports"].append(report)
        if kind == "sitemapindex":
            for child in locs:
                resolved, transport = guard.resolve_declared_sitemap(child)
                if resolved and resolved not in seen and resolved not in queue:
                    queue.append(resolved)
                if not resolved:
                    errors.append(f"nested_sitemap_{transport}")
        else:
            for page in locs:
                if _host(page):
                    enumerated.add(page)
                else:
                    errors.append("non_https_or_external_sitemap_page")
    if queue or len(enumerated) >= MAX_LOC_URLS:
        errors.append("traversal_budget_exhausted")
    urls = sorted(enumerated)
    counts = dict(sorted(Counter(classify_page(x) for x in urls).items()))
    candidates = [x for x in urls if classify_page(x) == "possible_catalogue_surface"]
    payload["robots"] = guard.evidence
    payload["enumerated_public_url_count"] = len(urls)
    payload["enumerated_url_sha256"] = hashlib.sha256(
        "\n".join(urls).encode("utf-8")
    ).hexdigest() if urls else None
    payload["classification_counts"] = counts
    payload["candidate_url_sample"] = _sample(candidates)
    payload["traversal_errors"] = sorted(set(errors))
    payload["traversal_complete"] = bool(initial) and not errors
    if not initial:
        payload["gate_assessment"] = "hold_no_discovered_public_sitemap"
    elif errors:
        payload["gate_assessment"] = "hold_public_enumeration_incomplete"
    elif candidates:
        payload["gate_assessment"] = "investigate_candidate_catalogue_semantics"
    else:
        payload["gate_assessment"] = "hold_no_proven_individual_film_records"
    return payload


def dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
