"""Fail-closed probe for the Mémoire Filmique shared catalogue.

This is a subordinate public surface for Jean Vigo analysis #80. It never
promotes the whole shared platform as Jean Vigo and never guesses record IDs.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT

MEMOIRE_FILMIQUE_HOME_URL = "https://www.memoirefilmiquedusud.eu/"
MEMOIRE_FILMIQUE_COLLECTION_URL = (
    "https://www.memoirefilmiquedusud.eu/collection"
)
MEMOIRE_FILMIQUE_ROBOTS_URL = (
    "https://www.memoirefilmiquedusud.eu/robots.txt"
)
MEMOIRE_FILMIQUE_PROBE_VERSION = "2026-10-memoire-filmique-probe-v1"
CRAWLER_TOKEN = "MemoriaAudiovisualRede"

_ALLOWED_HOSTS = {
    "memoirefilmiquedusud.eu",
    "www.memoirefilmiquedusud.eu",
}
_ITEM_PATH_RE = re.compile(
    r"^/(?:[a-z]{2}/)?collection/item/(?P<id>\d+)(?:-[^/?#]+)?/?$",
    re.I,
)
_RESULT_COUNT_PATTERNS = (
    re.compile(r"retourn[ée]\D{0,30}(\d[\d\s.,]*)\s+r[ée]sultat", re.I),
    re.compile(r"returned\D{0,30}(\d[\d\s.,]*)\s+result", re.I),
    re.compile(r"retornad[oa]\D{0,30}(\d[\d\s.,]*)\s+result", re.I),
)
_PROVIDER_LABELS = {
    "lieu de conservation",
    "film archive",
    "procedencia",
    "arxiu",
    "archivo",
}
_TYPE_LABELS = {
    "type de document",
    "type",
    "tipo de documento",
}
_FILM_VALUE_MARKERS = {"film", "película", "pellicula"}
_CHALLENGE_MARKERS = (
    "verification in progress",
    "prove you are human",
    "slide the button",
    "vérification en cours",
)
_MAX_PAGINATION_PAGES = 20
_MAX_SEMANTIC_SAMPLE = 16


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
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
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
    matches: list[tuple[int, bool]] = []
    for group in selected:
        for allowance, pattern in group["rules"]:
            if _rule_regex(pattern).search(target):
                score = len(pattern.rstrip("$").replace("*", ""))
                matches.append((score, allowance))
    if not matches:
        return True
    longest = max(score for score, _ in matches)
    return any(allowed for score, allowed in matches if score == longest)


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
        if (
            parsed.scheme.lower() != "https"
            or parsed.netloc.lower() not in _ALLOWED_HOSTS
        ):
            return ProbeResponse(
                requested_url,
                current_url,
                getattr(response, "status_code", None),
                "",
                "",
                "redirect_target_outside_authorized_origin",
            )
        if robots_text is not None and not robots_allowed(
            robots_text,
            CRAWLER_TOKEN,
            current_url,
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


def _challenge_detected(text: str) -> bool:
    lowered = _clean(text, limit=5000).lower()
    return any(marker in lowered for marker in _CHALLENGE_MARKERS)


def _canonical_item_url(url: str) -> str | None:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS:
        return None
    if not _ITEM_PATH_RE.match(parsed.path):
        return None
    return urlunparse(
        (
            "https",
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            "",
            "",
        )
    )


def _parse_int(value: str) -> int | None:
    digits = re.sub(r"\D", "", value or "")
    return int(digits) if digits else None


def _is_unfiltered_pagination(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or parsed.netloc.lower() not in _ALLOWED_HOSTS:
        return False
    path = parsed.path.lower().rstrip("/")
    if not (
        path.endswith("/collection")
        or path.endswith("/collection/default")
    ):
        return False
    query = parse_qs(parsed.query, keep_blank_values=True)
    if "page" not in query:
        return False
    for key, values in query.items():
        lowered = key.lower()
        if lowered.startswith("refine") or lowered.startswith("unrefine"):
            return False
        if lowered.startswith("geo_") or lowered == "fulltext":
            return False
        if lowered == "search" and any(str(value).strip() for value in values):
            return False
    return True


def parse_collection_page(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    visible = _clean(soup.get_text(" ", strip=True), limit=30000)
    result_count = None
    for pattern in _RESULT_COUNT_PATTERNS:
        match = pattern.search(visible)
        if match:
            result_count = _parse_int(match.group(1))
            break

    item_urls: set[str] = set()
    pagination_urls: set[str] = set()
    jean_vigo_filter_hints: list[dict[str, str]] = []

    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(page_url, anchor.get("href", ""))
        canonical = _canonical_item_url(absolute)
        if canonical:
            item_urls.add(canonical)
        elif _is_unfiltered_pagination(absolute):
            pagination_urls.add(absolute)
        if "institut jean vigo" in _clean(
            anchor.get_text(" ", strip=True)
        ).lower():
            jean_vigo_filter_hints.append(
                {
                    "kind": "link",
                    "url": absolute,
                    "label": _clean(anchor.get_text(" ", strip=True)),
                }
            )

    for select in soup.find_all("select"):
        name = _clean(select.get("name", ""))
        for option in select.find_all("option"):
            label = _clean(option.get_text(" ", strip=True))
            if "institut jean vigo" in label.lower():
                jean_vigo_filter_hints.append(
                    {
                        "kind": "select_option",
                        "field": name,
                        "value": _clean(option.get("value", "")),
                        "label": label,
                    }
                )

    return {
        "challenge_detected": _challenge_detected(html_text),
        "reported_result_count": result_count,
        "item_urls": sorted(item_urls),
        "pagination_urls": sorted(pagination_urls),
        "jean_vigo_filter_hints": jean_vigo_filter_hints[:20],
    }


def _label_value_pairs(soup: BeautifulSoup) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for dt in soup.find_all("dt"):
        dd = dt.find_next_sibling("dd")
        if dd is not None:
            pairs.append(
                (
                    _clean(dt.get_text(" ", strip=True)).lower().strip(" :"),
                    _clean(dd.get_text(" ", strip=True)),
                )
            )
    for row in soup.find_all("tr"):
        th = row.find("th")
        td = row.find("td")
        if th is not None and td is not None:
            pairs.append(
                (
                    _clean(th.get_text(" ", strip=True)).lower().strip(" :"),
                    _clean(td.get_text(" ", strip=True)),
                )
            )
    return pairs


def parse_item_page(html_text: str, page_url: str) -> dict[str, Any]:
    soup = BeautifulSoup(html_text or "", "html.parser")
    heading = soup.find("h1")
    title = _clean(
        heading.get_text(" ", strip=True)
        if heading is not None
        else (soup.title.get_text(" ", strip=True) if soup.title else "")
    )
    pairs = _label_value_pairs(soup)
    provider = ""
    document_type = ""
    metadata_labels: set[str] = set()
    for label, value in pairs:
        metadata_labels.add(label)
        if label in _PROVIDER_LABELS:
            provider = value
        if label in _TYPE_LABELS:
            document_type = value

    if not provider:
        visible = _clean(soup.get_text("\n", strip=True), limit=25000)
        provider_match = re.search(
            r"(?:Lieu de conservation|Film archive|Procedencia)\s*[:\n]\s*"
            r"([^\n]{2,160})",
            visible,
            flags=re.I,
        )
        if provider_match:
            provider = _clean(provider_match.group(1))

    type_is_film = any(
        marker in document_type.lower()
        for marker in _FILM_VALUE_MARKERS
    )
    film_metadata_signals = sum(
        1
        for family in (
            {"année", "date", "fecha"},
            {"durée", "length", "duración"},
            {"description matérielle", "gauge", "formato"},
            {"réalisateur/auteur", "director", "réalisateur"},
        )
        if metadata_labels & family
    )
    item_match = _ITEM_PATH_RE.match(urlparse(page_url).path)
    return {
        "title": title,
        "item_id": item_match.group("id") if item_match else "",
        "provider": provider,
        "document_type": document_type,
        "film_semantics_confirmed": bool(title)
        and type_is_film
        and film_metadata_signals >= 2,
        "metadata_labels": sorted(metadata_labels)[:30],
        "challenge_detected": _challenge_detected(html_text),
    }


def _deterministic_sample(urls: list[str], limit: int) -> list[str]:
    ordered = sorted(set(urls), key=lambda url: int(_ITEM_PATH_RE.match(
        urlparse(url).path
    ).group("id")))
    if len(ordered) <= limit:
        return ordered
    if limit <= 1:
        return [ordered[0]]
    indices = {
        round(index * (len(ordered) - 1) / (limit - 1))
        for index in range(limit)
    }
    return [ordered[index] for index in sorted(indices)]


def _evaluate_robots(session: requests.Session) -> tuple[dict[str, Any], str]:
    response = fetch_public_url(session, MEMOIRE_FILMIQUE_ROBOTS_URL)
    result: dict[str, Any] = {
        "url": MEMOIRE_FILMIQUE_ROBOTS_URL,
        "status_code": response.status_code,
        "error": response.error,
        "mode": None,
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
    return result, text


def enumerate_collection(
    session: requests.Session,
    robots_text: str,
    *,
    max_pages: int = _MAX_PAGINATION_PAGES,
) -> dict[str, Any]:
    queue = [MEMOIRE_FILMIQUE_COLLECTION_URL]
    seen: set[str] = set()
    item_urls: set[str] = set()
    page_reports: list[dict[str, Any]] = []
    reported_total = None
    filter_hints: list[dict[str, str]] = []
    truncated = False

    while queue:
        if len(seen) >= max_pages:
            truncated = True
            break
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        response = fetch_public_url(
            session,
            url,
            robots_text=robots_text if robots_text else None,
        )
        report: dict[str, Any] = {
            "url": url,
            "final_url": response.final_url,
            "status_code": response.status_code,
            "error": response.error,
        }
        if response.error or response.status_code != 200:
            report["status"] = "fetch_failed"
            page_reports.append(report)
            continue
        parsed = parse_collection_page(
            response.text,
            response.final_url or url,
        )
        report.update(
            {
                "status": (
                    "challenge"
                    if parsed["challenge_detected"]
                    else "ok"
                ),
                "reported_result_count": parsed["reported_result_count"],
                "item_count": len(parsed["item_urls"]),
                "pagination_count": len(parsed["pagination_urls"]),
                "item_sample": parsed["item_urls"][:8],
            }
        )
        page_reports.append(report)
        if parsed["challenge_detected"]:
            continue
        if parsed["reported_result_count"] is not None:
            if reported_total is None:
                reported_total = parsed["reported_result_count"]
            elif reported_total != parsed["reported_result_count"]:
                report["count_drift"] = True
        item_urls.update(parsed["item_urls"])
        filter_hints.extend(parsed["jean_vigo_filter_hints"])
        for child in parsed["pagination_urls"]:
            if child not in seen and child not in queue:
                queue.append(child)

    complete = (
        reported_total is not None
        and len(item_urls) == reported_total
        and not truncated
        and all(row.get("status") == "ok" for row in page_reports)
        and not any(row.get("count_drift") for row in page_reports)
    )
    return {
        "reported_result_count": reported_total,
        "unique_item_count": len(item_urls),
        "enumeration_complete": complete,
        "traversal_truncated": truncated,
        "page_count": len(seen),
        "pages": page_reports,
        "item_urls": sorted(item_urls),
        "jean_vigo_filter_hints": filter_hints[:30],
    }


def run_memoire_filmique_probe(
    session: requests.Session | None = None,
) -> dict[str, Any]:
    session = session or _session()
    robots, robots_text = _evaluate_robots(session)
    payload: dict[str, Any] = {
        "probe_version": MEMOIRE_FILMIQUE_PROBE_VERSION,
        "surface_role": "official_shared_platform_subordinate_to_jean_vigo_80",
        "robots": robots,
        "enumeration": {},
        "semantic_sample": [],
        "semantic_sample_size": 0,
        "semantic_confirmed_count": 0,
        "provider_present_count": 0,
        "jean_vigo_provider_count": 0,
        "providers_observed": [],
        "gate_assessment": "hold_external_surface_unverified",
        "next_action": "keep_jean_vigo_80_open",
    }
    if robots["mode"] == "unverifiable":
        payload["gate_assessment"] = "hold_external_surface_robots_unverifiable"
        return payload
    if robots_text and not robots_allowed(
        robots_text,
        CRAWLER_TOKEN,
        MEMOIRE_FILMIQUE_COLLECTION_URL,
    ):
        payload["gate_assessment"] = "hold_external_surface_collection_blocked"
        return payload

    enumeration = enumerate_collection(session, robots_text)
    payload["enumeration"] = {
        key: value
        for key, value in enumeration.items()
        if key != "item_urls"
    }
    challenge_seen = any(
        row.get("status") == "challenge"
        for row in enumeration.get("pages", [])
    )
    if not enumeration["enumeration_complete"]:
        if challenge_seen:
            payload["gate_assessment"] = (
                "hold_external_surface_antibot_challenge"
            )
            payload["next_action"] = (
                "do_not_bypass_challenge_retest_or_seek_public_export"
            )
        else:
            payload["gate_assessment"] = (
                "hold_external_surface_enumeration_incomplete"
            )
            payload["next_action"] = (
                "protocol_external_surface_without_partial_corpus"
            )
        return payload

    sample_urls = _deterministic_sample(
        enumeration["item_urls"],
        _MAX_SEMANTIC_SAMPLE,
    )
    providers: set[str] = set()
    for url in sample_urls:
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
        else:
            parsed = parse_item_page(
                response.text,
                response.final_url or url,
            )
            row.update(parsed)
            row["status"] = (
                "challenge"
                if parsed["challenge_detected"]
                else "ok"
            )
            if parsed["provider"]:
                providers.add(parsed["provider"])
        payload["semantic_sample"].append(row)

    rows = payload["semantic_sample"]
    payload["semantic_sample_size"] = len(rows)
    payload["semantic_confirmed_count"] = sum(
        1
        for row in rows
        if row.get("status") == "ok"
        and row.get("film_semantics_confirmed")
    )
    payload["provider_present_count"] = sum(
        1
        for row in rows
        if row.get("status") == "ok" and row.get("provider")
    )
    payload["jean_vigo_provider_count"] = sum(
        1
        for row in rows
        if "institut jean vigo" in str(row.get("provider", "")).lower()
    )
    payload["providers_observed"] = sorted(providers)

    sample_complete = (
        rows
        and all(row.get("status") == "ok" for row in rows)
        and payload["semantic_confirmed_count"] == len(rows)
    )
    provenance_parseable = (
        sample_complete
        and payload["provider_present_count"] == len(rows)
    )
    if provenance_parseable:
        payload["gate_assessment"] = (
            "shared_platform_enumeration_confirmed_staged_provenance_scan_required"
        )
        payload["next_action"] = (
            "engineer_staged_collector_and_isolate_institut_jean_vigo_by_provider"
        )
    elif sample_complete:
        payload["gate_assessment"] = (
            "hold_shared_platform_provider_isolation_unconfirmed"
        )
        payload["next_action"] = (
            "validate_provider_field_before_any_jean_vigo_incorporation"
        )
    else:
        payload["gate_assessment"] = (
            "hold_external_surface_semantic_validation_incomplete"
        )
        payload["next_action"] = (
            "protocol_external_surface_without_partial_corpus"
        )
    return payload


def dumps_probe(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
