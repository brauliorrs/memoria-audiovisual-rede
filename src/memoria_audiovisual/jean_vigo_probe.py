"""Fail-closed public-surface probe for the Jean Vigo Institute."""
from __future__ import annotations

import gzip
import io
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
_ALLOWED_HOSTS = {_ALLOWED_HOST, "inst-jeanvigo.eu"}
_SITEMAP_DIRECTIVE_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")
_XML_LOC_OPEN_RE = re.compile(
    r"<(?:[A-Za-z_][\w.-]*:)?loc\b[^>]*>",
    re.I,
)
_MAX_SITEMAP_DECOMPRESSED_BYTES = 8 * 1024 * 1024
_MAX_COLLECTION_AUDIT_PAGES = 40
_COLLECTION_PATH_TOKEN = "collections-cinematheque-perpignan-institut-jean-vigo"
_ARCHIVAL_IDENTIFIER_LABELS = {
    "cote",
    "reference",
    "référence",
    "inventaire",
    "numero d'inventaire",
    "numéro d'inventaire",
}
_FILM_METADATA_LABELS = {
    "realisateur",
    "réalisateur",
    "realisation",
    "réalisation",
    "annee",
    "année",
    "date",
    "duree",
    "durée",
    "format",
    "support",
    "metrage",
    "métrage",
    "production",
    "synopsis",
}
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
    body: bytes = b""


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
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS:
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
            getattr(response, "content", b"") or b"",
        )
    return ProbeResponse(
        requested_url,
        current_url,
        getattr(response, "status_code", None),
        "",
        "",
        "redirect_limit_exceeded",
    )


def decode_sitemap_response(
    response: ProbeResponse,
    *,
    max_decompressed_bytes: int = _MAX_SITEMAP_DECOMPRESSED_BYTES,
) -> tuple[str | None, str | None]:
    """Decode a sitemap response, including raw application/gzip bodies."""
    raw = response.body or b""
    content_type = (response.content_type or "").split(";", 1)[0].strip().lower()
    path = urlparse(response.final_url or response.requested_url).path.lower()
    gzip_expected = path.endswith(".gz") or content_type in {
        "application/gzip",
        "application/x-gzip",
    }

    if raw.startswith(b"\x1f\x8b"):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
                decoded = stream.read(max_decompressed_bytes + 1)
        except (OSError, EOFError) as exc:
            return None, f"gzip_decode_failed:{type(exc).__name__}"
        if len(decoded) > max_decompressed_bytes:
            return None, "gzip_decompressed_too_large"
        try:
            return decoded.decode("utf-8-sig"), None
        except UnicodeDecodeError:
            return None, "gzip_utf8_decode_failed"

    if gzip_expected and raw and not response.text.lstrip().startswith("<"):
        return None, "gzip_body_missing_magic"

    text = response.text or ""
    if len(text.encode("utf-8", errors="ignore")) > max_decompressed_bytes:
        return None, "sitemap_text_too_large"
    return text, None


def resolve_declared_sitemap_url(
    session: requests.Session,
    url: str,
) -> tuple[str | None, dict[str, Any]]:
    """Resolve a robots-declared sitemap without accepting HTTP content.

    HTTPS declarations pass through unchanged. An explicit HTTP declaration may
    be contacted only to observe a redirect; its response body is never used.
    The redirect must land on HTTPS at the same authorized host.
    """
    parsed = urlparse(url)
    evidence: dict[str, Any] = {
        "declared_url": url,
        "resolved_url": None,
        "status": None,
        "http_status": None,
    }
    if parsed.netloc.lower() not in _ALLOWED_HOSTS:
        evidence["status"] = "rejected_origin"
        return None, evidence
    if parsed.scheme.lower() == "https":
        evidence["resolved_url"] = url
        evidence["status"] = "https_declared"
        return url, evidence
    if parsed.scheme.lower() != "http":
        evidence["status"] = "rejected_scheme"
        return None, evidence

    try:
        response = session.get(
            url,
            timeout=(8, REQUEST_TIMEOUT),
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        evidence["status"] = "http_redirect_probe_failed"
        evidence["error"] = f"{type(exc).__name__}: {exc}"
        return None, evidence

    evidence["http_status"] = response.status_code
    if response.status_code not in {301, 302, 303, 307, 308}:
        evidence["status"] = "http_content_not_accepted"
        return None, evidence
    location = response.headers.get("location", "")
    if not location:
        evidence["status"] = "redirect_without_location"
        return None, evidence

    target = urljoin(url, location)
    target_parsed = urlparse(target)
    if (
        target_parsed.scheme.lower() != "https"
        or target_parsed.netloc.lower() not in _ALLOWED_HOSTS
    ):
        evidence["status"] = "redirect_target_not_authorized_https"
        evidence["redirect_target"] = target
        return None, evidence

    evidence["resolved_url"] = target
    evidence["status"] = "http_redirected_to_authorized_https"
    return target, evidence


def parse_surface_html(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    same_host: list[str] = []
    external: list[str] = []
    forms: list[dict[str, Any]] = []
    scripts: list[str] = []
    for anchor in scope.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        if parsed.netloc.lower() in _ALLOWED_HOSTS:
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
        if urlparse(absolute).netloc.lower() in _ALLOWED_HOSTS:
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


def _normalized_label(value: Any) -> str:
    text = _clean(value).lower().strip(" :;.-")
    return text


def _matches_label_family(label: str, family: set[str]) -> bool:
    return any(
        label == item
        or label.startswith(item + " ")
        or label.startswith(item + ":")
        for item in family
    )


def _text_markers(text: str, family: set[str]) -> list[str]:
    found: list[str] = []
    for item in sorted(family):
        if re.search(rf"(?<!\w){re.escape(item)}(?!\w)", text, flags=re.I):
            found.append(item)
    return found


def _content_scope(soup: BeautifulSoup) -> Any:
    for selector in (
        "main",
        "article",
        ".entry-content",
        ".post-content",
        ".page-content",
        "#content",
    ):
        node = soup.select_one(selector)
        if node is not None:
            return node
    return soup.body or soup


def _unstructured_record_evidence(scope: Any) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    text_film_family = _FILM_METADATA_LABELS - {"date"}
    for node in scope.find_all(["p", "li", "dd", "td"]):
        text = _clean(node.get_text(" ", strip=True))
        if not text or len(text) > 1600:
            continue
        lowered = text.lower()
        identifiers = _text_markers(lowered, _ARCHIVAL_IDENTIFIER_LABELS)
        film_markers = _text_markers(lowered, text_film_family)
        if identifiers and len(film_markers) >= 3:
            evidence.append(
                {
                    "identifier_markers": identifiers,
                    "film_markers": film_markers,
                    "excerpt": _clean(text, limit=320),
                }
            )
    if evidence:
        return evidence[:5]

    visible = _clean(scope.get_text(" ", strip=True))
    if 0 < len(visible) <= 3000:
        lowered = visible.lower()
        identifiers = _text_markers(lowered, _ARCHIVAL_IDENTIFIER_LABELS)
        film_markers = _text_markers(lowered, text_film_family)
        if identifiers and len(film_markers) >= 3:
            return [
                {
                    "identifier_markers": identifiers,
                    "film_markers": film_markers,
                    "excerpt": _clean(visible, limit=320),
                }
            ]
    return []


def parse_collection_page_semantics(
    html_text: str,
    page_url: str,
) -> dict[str, Any]:
    """Classify one sitemap-derived collection page conservatively."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    scope = _content_scope(soup)
    labels: set[str] = set()
    for node in scope.find_all(["dt", "th"]):
        label = _normalized_label(node.get_text(" ", strip=True))
        if label:
            labels.add(label)
    for node in scope.find_all(["strong", "b"]):
        text = _normalized_label(node.get_text(" ", strip=True))
        if (
            _matches_label_family(text, _ARCHIVAL_IDENTIFIER_LABELS)
            or _matches_label_family(text, _FILM_METADATA_LABELS)
        ):
            labels.add(text)

    identifiers = sorted(
        label
        for label in labels
        if _matches_label_family(label, _ARCHIVAL_IDENTIFIER_LABELS)
    )
    film_labels = sorted(
        label
        for label in labels
        if _matches_label_family(label, _FILM_METADATA_LABELS)
    )
    visible_text = _clean(scope.get_text(" ", strip=True), limit=30000).lower()
    text_identifiers = _text_markers(
        visible_text,
        _ARCHIVAL_IDENTIFIER_LABELS,
    )
    text_film_family = _FILM_METADATA_LABELS - {"date"}
    text_film_markers = _text_markers(visible_text, text_film_family)
    unstructured_evidence = _unstructured_record_evidence(scope)

    same_host_children: set[str] = set()
    external_archive_links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            continue
        host = parsed.netloc.lower()
        if (
            host in _ALLOWED_HOSTS
            and _COLLECTION_PATH_TOKEN in parsed.path.lower()
            and absolute.rstrip("/") != page_url.rstrip("/")
        ):
            same_host_children.add(absolute)
        if (
            "memoirefilmiquedusud" in host
            or "cine-ressources" in absolute.lower()
            or host == "purl.org"
        ):
            external_archive_links.add(absolute)

    schema_types: set[str] = set()
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        try:
            value = json.loads(raw)
        except (TypeError, ValueError):
            continue
        stack = [value]
        while stack:
            current = stack.pop()
            if isinstance(current, dict):
                type_value = current.get("@type")
                if isinstance(type_value, str):
                    schema_types.add(type_value.lower())
                elif isinstance(type_value, list):
                    schema_types.update(
                        str(item).lower() for item in type_value
                    )
                stack.extend(current.values())
            elif isinstance(current, list):
                stack.extend(current)

    strong_record = bool(identifiers) and len(film_labels) >= 2
    structured_candidate = (
        not strong_record
        and (
            len(film_labels) >= 3
            or bool(schema_types & {"movie", "videoobject"})
        )
    )
    unstructured_candidate = (
        not strong_record
        and not structured_candidate
        and bool(unstructured_evidence)
    )
    if strong_record:
        semantic_class = "individual_archival_record_confirmed"
    elif structured_candidate:
        semantic_class = "individual_archival_record_candidate"
    elif unstructured_candidate:
        semantic_class = "unstructured_archival_record_candidate"
    elif len(same_host_children) >= 3:
        semantic_class = "collection_index_or_hub"
    elif external_archive_links:
        semantic_class = "external_archive_pointer"
    else:
        semantic_class = "institutional_collection_page"

    heading = scope.find("h1") or soup.find("h1")
    title = _clean(
        heading.get_text(" ", strip=True)
        if heading
        else (soup.title.get_text(" ", strip=True) if soup.title else "")
    )
    return {
        "title": title,
        "semantic_class": semantic_class,
        "identifier_labels": identifiers,
        "film_metadata_labels": film_labels,
        "text_identifier_markers": text_identifiers,
        "text_film_markers": text_film_markers,
        "unstructured_record_evidence": unstructured_evidence,
        "schema_types": sorted(schema_types)[:20],
        "same_host_collection_child_count": len(same_host_children),
        "same_host_collection_child_sample": sorted(same_host_children)[:12],
        "external_archive_links": sorted(external_archive_links)[:20],
    }


def audit_collection_pages(
    session: requests.Session,
    urls: list[str],
    robots_text: str,
    *,
    max_pages: int = _MAX_COLLECTION_AUDIT_PAGES,
) -> tuple[list[dict[str, Any]], bool]:
    ordered = sorted(set(urls))
    truncated = len(ordered) > max_pages
    selected = ordered[:max_pages]
    reports: list[dict[str, Any]] = []
    for url in selected:
        response = fetch_public_url(
            session,
            url,
            robots_text=robots_text if robots_text else None,
        )
        row: dict[str, Any] = {
            "url": url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "error": response.error,
        }
        if response.error or response.status_code != 200:
            row["status"] = "fetch_failed"
            reports.append(row)
            continue
        row.update(
            parse_collection_page_semantics(
                response.text,
                response.final_url or url,
            )
        )
        row["status"] = "ok"
        reports.append(row)
    return reports, truncated


def _local_tag(tag: str) -> str:
    value = str(tag).rsplit("}", 1)[-1]
    return value.rsplit(":", 1)[-1].lower()


def _append_sitemap_loc(
    loc_value: str,
    container_kind: str,
    *,
    urls: list[str],
    same_host_pages: list[str],
    nested: list[str],
    rejected: list[str],
) -> None:
    loc_value = _clean(loc_value)
    if not loc_value:
        return
    urls.append(loc_value)
    parsed = urlparse(loc_value)
    if parsed.netloc.lower() not in _ALLOWED_HOSTS:
        rejected.append(loc_value)
        return
    if container_kind == "sitemap":
        if parsed.scheme.lower() not in {"http", "https"}:
            rejected.append(loc_value)
            return
        nested.append(loc_value)
        return
    if container_kind != "url":
        return
    if parsed.scheme.lower() != "https":
        rejected.append(loc_value)
        return
    if parsed.path.lower().endswith(_ASSET_SUFFIXES):
        return
    same_host_pages.append(loc_value)


def _tag_parts(tag: str) -> tuple[str | None, str]:
    value = str(tag)
    if value.startswith("{") and "}" in value:
        namespace, local = value[1:].split("}", 1)
        return namespace, local.lower()
    return None, _local_tag(value)


def _parse_sitemap_strict(
    xml_text: str,
) -> tuple[list[tuple[str, str]], str, int]:
    root = ET.fromstring(xml_text or "")
    root_namespace, root_kind = _tag_parts(root.tag)
    raw_loc_count = sum(
        1
        for node in root.iter()
        if _tag_parts(node.tag) == (root_namespace, "loc")
    )
    pairs: list[tuple[str, str]] = []
    for container in list(root):
        container_namespace, container_kind = _tag_parts(container.tag)
        if container_namespace != root_namespace:
            continue
        if root_kind == "sitemapindex" and container_kind != "sitemap":
            continue
        if root_kind == "urlset" and container_kind != "url":
            continue
        if container_kind not in {"sitemap", "url"}:
            continue
        for child in list(container):
            child_namespace, child_kind = _tag_parts(child.tag)
            if child_namespace == root_namespace and child_kind == "loc":
                pairs.append((container_kind, _clean(child.text)))
                break
    return pairs, root_kind, raw_loc_count


def _xml_entity_unescape(value: str) -> str:
    replacements = (
        ("&quot;", '"'),
        ("&apos;", "'"),
        ("&lt;", "<"),
        ("&gt;", ">"),
        ("&amp;", "&"),
    )
    for encoded, decoded in replacements:
        value = value.replace(encoded, decoded)
    return value


def _parse_sitemap_tolerant(
    xml_text: str,
) -> tuple[list[tuple[str, str]], str, int]:
    """Recover sitemap roles from tags without HTML entity reinterpretation."""
    text = re.sub(r"<!--.*?-->", "", xml_text or "", flags=re.S)
    root_matches = [
        kind
        for kind in ("sitemapindex", "urlset")
        if re.search(
            rf"<(?:[A-Za-z_][\w.-]*:)?{kind}\b[^>]*>",
            text,
            flags=re.I,
        )
    ]
    raw_loc_count = len(_XML_LOC_OPEN_RE.findall(text))
    if len(root_matches) != 1:
        return [], "ambiguous", raw_loc_count

    root_kind = root_matches[0]
    root_match = re.search(
        rf"<(?:[A-Za-z_][\w.-]*:)?{root_kind}\b[^>]*>"
        rf"(?P<body>.*?)"
        rf"</(?:[A-Za-z_][\w.-]*:)?{root_kind}\s*>",
        text,
        flags=re.I | re.S,
    )
    if not root_match:
        return [], root_kind, raw_loc_count

    expected_container = "sitemap" if root_kind == "sitemapindex" else "url"
    container_pattern = re.compile(
        rf"<(?:[A-Za-z_][\w.-]*:)?{expected_container}\b[^>]*>"
        rf"(?P<body>.*?)"
        rf"</(?:[A-Za-z_][\w.-]*:)?{expected_container}\s*>",
        flags=re.I | re.S,
    )
    loc_pattern = re.compile(
        r"<(?:[A-Za-z_][\w.-]*:)?loc\b[^>]*>"
        r"(?P<value>.*?)"
        r"</(?:[A-Za-z_][\w.-]*:)?loc\s*>",
        flags=re.I | re.S,
    )

    pairs: list[tuple[str, str]] = []
    for container in container_pattern.finditer(root_match.group("body")):
        loc = loc_pattern.search(container.group("body"))
        if not loc:
            continue
        raw_value = re.sub(r"<[^>]+>", "", loc.group("value"))
        pairs.append(
            (
                expected_container,
                _clean(_xml_entity_unescape(raw_value)),
            )
        )
    return pairs, root_kind, raw_loc_count


def parse_sitemap(xml_text: str) -> dict[str, Any]:
    same_host_pages: list[str] = []
    nested: list[str] = []
    rejected: list[str] = []
    urls: list[str] = []
    strict_error: str | None = None
    normalized_xml = (xml_text or "").lstrip("\ufeff \t\r\n")

    try:
        pairs, root_kind, raw_loc_count = _parse_sitemap_strict(normalized_xml)
        parse_mode = "strict_xml"
    except ET.ParseError as exc:
        strict_error = _clean(str(exc), limit=300)
        pairs, root_kind, raw_loc_count = _parse_sitemap_tolerant(normalized_xml)
        parse_mode = "tolerant_structural"

    for container_kind, loc_value in pairs:
        _append_sitemap_loc(
            loc_value,
            container_kind,
            urls=urls,
            same_host_pages=same_host_pages,
            nested=nested,
            rejected=rejected,
        )

    attributed_count = len(pairs)
    ambiguous_loc_count = max(raw_loc_count - attributed_count, 0)
    root_valid = root_kind in {"sitemapindex", "urlset"}
    recovery_failed = (not root_valid) or (
        bool(raw_loc_count) and ambiguous_loc_count > 0
    )

    return {
        "url_count": len(urls),
        "raw_loc_count": raw_loc_count,
        "attributed_loc_count": attributed_count,
        "ambiguous_loc_count": ambiguous_loc_count,
        "same_host_page_count": len(set(same_host_pages)),
        "same_host_pages": sorted(set(same_host_pages)),
        "nested_sitemaps": sorted(set(nested)),
        "rejected_urls": sorted(set(rejected)),
        "parse_mode": parse_mode,
        "root_kind": root_kind,
        "root_valid": root_valid,
        "strict_parse_error": strict_error,
        "parse_error": recovery_failed,
    }


def classify_public_url(url: str) -> str:
    path = urlparse(url).path.lower()
    if path.startswith("/agenda/"):
        return "agenda_or_programming"
    if (
        path.startswith("/actualites/")
        or path.startswith("/mots-cles/")
        or path.startswith("/categories/")
    ):
        return "editorial_page"
    if _COLLECTION_PATH_TOKEN in path:
        return "institutional_collection_page"
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
    queue: list[str] = []
    seen: set[str] = set()
    reports: list[dict[str, Any]] = []
    pages: list[str] = []
    truncated = False
    for declared_url in sitemap_urls:
        resolved, transport = resolve_declared_sitemap_url(session, declared_url)
        reports.append({"transport": transport, "status": "transport_checked"})
        if resolved and resolved not in queue:
            queue.append(resolved)
    while queue:
        if len(seen) >= max_sitemaps:
            truncated = True
            break
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS:
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
        sitemap_text, decode_error = decode_sitemap_response(response)
        if decode_error or sitemap_text is None:
            report["status"] = "decode_failed"
            report["decode_error"] = decode_error
            reports.append(report)
            continue
        parsed_map = parse_sitemap(sitemap_text)
        report.update(
            {
                key: value
                for key, value in parsed_map.items()
                if key not in {"same_host_pages", "nested_sitemaps"}
            }
        )
        report["same_host_page_sample"] = parsed_map["same_host_pages"][:20]
        report["nested_sitemap_sample"] = parsed_map["nested_sitemaps"][:20]
        if parsed_map["parse_error"]:
            report["status"] = "parse_failed"
            reports.append(report)
            continue
        report["status"] = "ok"
        reports.append(report)
        pages.extend(parsed_map["same_host_pages"])
        for child in parsed_map["nested_sitemaps"]:
            resolved_child, transport = resolve_declared_sitemap_url(session, child)
            reports.append(
                {
                    "url": child,
                    "transport": transport,
                    "status": "nested_transport_checked",
                }
            )
            if (
                resolved_child
                and resolved_child not in seen
                and resolved_child not in queue
            ):
                queue.append(resolved_child)
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
        "collection_pages": [],
        "collection_page_audit": [],
        "collection_audit_truncated": False,
        "collection_semantic_counts": {},
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
        collection_urls: list[str] = []
        for page in pages:
            key = classify_public_url(page)
            counts[key] = counts.get(key, 0) + 1
            if key == "institutional_collection_page":
                collection_urls.append(page)
        payload["classification_counts"] = counts
        payload["collection_pages"] = sorted(set(collection_urls))

        if (
            collection_urls
            and not payload["sitemap_traversal_truncated"]
        ):
            audit, audit_truncated = audit_collection_pages(
                session,
                collection_urls,
                robots_text,
            )
            payload["collection_page_audit"] = audit
            payload["collection_audit_truncated"] = audit_truncated
            semantic_counts: dict[str, int] = {}
            for row in audit:
                key = row.get("semantic_class", "fetch_failed")
                semantic_counts[key] = semantic_counts.get(key, 0) + 1
                for link in row.get("external_archive_links", []):
                    external_hints.add(link)
            payload["collection_semantic_counts"] = semantic_counts

    payload["external_archive_hints"] = sorted(external_hints)
    collection_count = len(payload["collection_pages"])
    audit_rows = payload["collection_page_audit"]
    audit_complete = (
        collection_count > 0
        and not payload["sitemap_traversal_truncated"]
        and not payload["collection_audit_truncated"]
        and len(audit_rows) == collection_count
        and all(row.get("status") == "ok" for row in audit_rows)
    )
    confirmed_records = payload["collection_semantic_counts"].get(
        "individual_archival_record_confirmed", 0
    )
    record_candidates = (
        payload["collection_semantic_counts"].get(
            "individual_archival_record_candidate", 0
        )
        + payload["collection_semantic_counts"].get(
            "unstructured_archival_record_candidate", 0
        )
    )

    if confirmed_records and audit_complete:
        payload["gate_assessment"] = (
            "bounded_public_record_enumeration_confirmed_staged_required"
        )
        payload["next_action"] = (
            "engineer_staged_collector_from_sitemap_confirmed_records"
        )
    elif record_candidates and audit_complete:
        payload["gate_assessment"] = (
            "investigate_collection_record_candidates_before_staged"
        )
        payload["next_action"] = (
            "validate_candidate_record_metadata_before_staged"
        )
    elif collection_count and not audit_complete:
        payload["gate_assessment"] = "hold_collection_semantics_incomplete"
        payload["next_action"] = (
            "repair_or_repeat_collection_semantic_audit_before_decision"
        )
    elif collection_count and audit_complete:
        payload["gate_assessment"] = (
            "hold_primary_site_no_enumerable_archival_records"
        )
        payload["next_action"] = (
            "protocol_primary_site_and_assess_external_archive_separately"
        )
    elif external_hints:
        payload["gate_assessment"] = "hold_primary_site_points_to_external_archive"
        payload["next_action"] = (
            "protocol_primary_site_and_assess_external_archive_as_separate_surface"
        )
    return payload


def dumps_probe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
