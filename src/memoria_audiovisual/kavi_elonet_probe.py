"""Fail-closed, low-impact public discovery of KAVI/Elonet/Finna (#82).

No harvested audiovisual bytes, guessed record identifiers or bulk API downloads.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT
from .jean_vigo_probe import robots_allowed

VERSION = "2026-10-kavi-elonet-probe-v1"
USER_AGENT = "MemoriaAudiovisualRede"
HOME = "https://kavi.fi/en/film/"
ELONET_FAQ = "https://elonet.finna.fi/Content/faq?lng=en-gb"
ELONET_FILMOGRAPHY = "https://elonet.finna.fi/Content/filmography"
API_ROOT = "https://api.finna.fi/v1/search"
ALLOWED_HOSTS = frozenset({
    "kavi.fi", "www.kavi.fi", "elonet.finna.fi",
    "kavi.finna.fi", "api.finna.fi",
})
SURFACES = (
    ("kavi_film_page", HOME),
    ("elonet_faq", ELONET_FAQ),
    ("elonet_filmography", ELONET_FILMOGRAPHY),
)
# Both shapes are explicitly described by the Finna API documentation.
FACET_QUERY = API_ROOT + "?" + urlencode({
    "lookfor": "", "limit": 0, "facet[]": "building",
})
SAMPLE_QUERY = API_ROOT + "?" + urlencode({
    "lookfor": "Salaviinanpolttajat", "limit": 2,
})
LIMIT_BYTES = 2_000_000
MAX_REDIRECTS = 5


def _host(url: str) -> str | None:
    p = urlparse(url)
    try:
        port = p.port
    except ValueError:
        return None
    if (p.scheme != "https" or p.hostname not in ALLOWED_HOSTS
        or port not in (None, 443) or p.username or p.password
        or p.fragment):
        return None
    return p.hostname


@dataclass(frozen=True)
class Fetch:
    requested: str
    final: str | None
    status: int | None
    text: str
    error: str | None
    mime: str = ""


class Guard:
    def __init__(self, session: requests.Session):
        self.session = session
        self.evidence: dict[str, dict[str, Any]] = {}
        self.rules: dict[str, str] = {}

    def robots(self, host: str) -> dict[str, Any]:
        if host in self.evidence:
            return self.evidence[host]
        url = f"https://{host}/robots.txt"
        row: dict[str, Any] = {"url": url, "mode": "unverifiable",
                               "status": None, "error": None}
        self.evidence[host] = row
        try:
            r = self.session.get(url, timeout=(8, REQUEST_TIMEOUT),
                                 allow_redirects=False)
        except requests.RequestException as ex:
            row["error"] = f"{type(ex).__name__}: {ex}"
            return row
        row["status"] = r.status_code
        if r.status_code in (404, 410):
            row["mode"] = "absent"
        elif r.status_code == 200:
            value = r.text or ""
            if value.strip() and "<html" not in value.lower():
                row["mode"] = "evaluated"
                self.rules[host] = value
            else:
                row["error"] = "robots_invalid_body"
        else:
            # Cross-host redirects are not a grant to crawl the new host.
            row["error"] = "robots_unverifiable_http_status"
        return row

    def permitted(self, url: str) -> bool:
        host = _host(url)
        if not host:
            return False
        p = self.robots(host)
        if p["mode"] == "unverifiable":
            return False
        return p["mode"] == "absent" or robots_allowed(
            self.rules[host], USER_AGENT, url,
        )

    def get(self, url: str) -> Fetch:
        requested = url
        seen: set[str] = set()
        for _ in range(MAX_REDIRECTS + 1):
            if not self.permitted(url):
                return Fetch(requested, url, None, "", "robots_or_origin_block")
            if url in seen:
                return Fetch(requested, url, None, "", "redirect_cycle")
            seen.add(url)
            try:
                r = self.session.get(url, timeout=(8, REQUEST_TIMEOUT),
                                     allow_redirects=False, stream=True)
            except requests.RequestException as ex:
                return Fetch(requested, url, None, "",
                             f"{type(ex).__name__}: {ex}")
            try:
                status = r.status_code
                if status in (301, 302, 303, 307, 308):
                    target = urljoin(url, r.headers.get("location", ""))
                    if not _host(target):
                        return Fetch(requested, target, status, "",
                                     "redirect_outside_https_scope")
                    url = target
                    continue
                if status != 200:
                    return Fetch(requested, url, status, "",
                                 "non_success_http_status")
                mime = r.headers.get("content-type", "")
                length = r.headers.get("content-length")
                if length and length.isdigit() and int(length) > LIMIT_BYTES:
                    return Fetch(requested, url, status, "",
                                 "body_size_limit", mime)
                # Stream just enough bytes; no unbounded download.
                body = bytearray()
                for chunk in r.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > LIMIT_BYTES:
                        return Fetch(requested, url, status, "",
                                     "body_size_limit", mime)
                encoding = r.encoding or "utf-8"
                return Fetch(requested, url, status,
                             bytes(body).decode(encoding, errors="replace"),
                             None, mime)
            finally:
                r.close()
        return Fetch(requested, url, None, "", "redirect_budget_exceeded")


def parse_public_page(html: str, base: str) -> dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    links = sorted({
        urljoin(base, anchor.get("href", ""))
        for anchor in soup.select("a[href]")
        if _host(urljoin(base, anchor.get("href", "")))
    })
    return {
        "title": title[:200],
        "same_origin_links_sample": links[:25],
        "same_origin_links_count": len(links),
        "mentions_elonet": "elonet" in soup.get_text(" ", strip=True).lower(),
    }


def _kavi_building_candidates(buildings: list[Any]) -> list[dict[str, Any]]:
    """Use only codes explicitly returned in the Finna building facet.

    KAVI merged into Kuvi in 2026; names and legacy IDs may coexist.
    This is discovery, not evidence of custody of an individual film.
    """
    found: list[dict[str, Any]] = []
    stack = list(buildings)
    while stack:
        item = stack.pop()
        if not isinstance(item, dict):
            continue
        value = item.get("value")
        translated = item.get("translated")
        if isinstance(value, str) and isinstance(translated, str):
            label = translated.casefold()
            tail = value.strip("/").split("/")[-1].casefold()
            if (
                tail in {"kavi", "kuvi", "elonet"}
                or label in {"kavi", "kuvi", "elonet"}
                or "kansallinen audiovisuaalinen instituutti" in label
                or "taide- ja kulttuurivirasto" in label
                or "finnish arts and culture agency" in label
            ):
                found.append({
                    "value": value,
                    "translated": translated,
                    "count": item.get("count"),
                })
        children = item.get("children")
        if isinstance(children, list):
            stack.extend(children)
    return sorted(found, key=lambda item: item["value"])


def _build_verified_facet_query(facet_code: str) -> str:
    """Build documented filter syntax only from a facet returned by the API."""
    if not facet_code or '"' in facet_code or len(facet_code) > 160:
        raise ValueError("unsafe_facet_code")
    return API_ROOT + "?" + urlencode([
        ("lookfor", ""), ("limit", "3"),
        ("filter[]", f'building:"{facet_code}"'),
    ])


def _video_format_candidates(record_rows: list[dict[str, Any]]) -> list[str]:
    """Use an observed Video format facet code, not a guessed API value."""
    values: set[str] = set()
    for row in record_rows:
        formats = row.get("formats", [])
        if not isinstance(formats, list):
            continue
        for item in formats:
            if not isinstance(item, dict):
                continue
            label = item.get("translated")
            value = item.get("value")
            if (
                isinstance(label, str) and label.casefold() == "video"
                and isinstance(value, str) and value.endswith("/Video/")
            ):
                values.add(value)
    return sorted(values)


def _build_verified_video_query(building: str, video_format: str) -> str:
    for term in (building, video_format):
        if not term or '"' in term or len(term) > 160:
            raise ValueError("unsafe_verified_facet")
    return API_ROOT + "?" + urlencode([
        ("lookfor", ""), ("limit", "3"),
        ("filter[]", f'building:"{building}"'),
        ("filter[]", f'format:"{video_format}"'),
    ])


def parse_finna_response(text: str, *, expect_facets: bool = False) -> dict[str, Any]:
    try:
        raw = json.loads(text)
    except (TypeError, json.JSONDecodeError) as ex:
        raise ValueError("invalid_finna_json") from ex
    if not isinstance(raw, dict):
        raise ValueError("finna_json_root_not_object")
    if raw.get("status") not in ("OK", "ok"):
        raise ValueError("finna_api_not_ok")
    count = raw.get("resultCount")
    if not isinstance(count, int) or isinstance(count, bool) or count < 0:
        raise ValueError("finna_result_count_invalid")
    records = raw.get("records", [])
    if not isinstance(records, list):
        raise ValueError("finna_records_not_list")
    ids = [row.get("id") for row in records if isinstance(row, dict)]
    if len(ids) != len(records) or any(not isinstance(i, str) or not i for i in ids):
        raise ValueError("finna_missing_record_ids")
    if len(ids) != len(set(ids)):
        raise ValueError("finna_duplicate_record_ids")
    facets = raw.get("facets", {})
    if expect_facets and (not isinstance(facets, dict)
                          or "building" not in facets):
        raise ValueError("finna_building_facet_missing")
    building = facets.get("building", []) if isinstance(facets, dict) else []
    if isinstance(building, dict):
        building = [building]
    if not isinstance(building, list):
        raise ValueError("finna_invalid_building_facet")
    # Do not treat resultCount or building count as harvested KAVI films.
    return {
        "total_claim": count,
        "returned_records": len(records),
        "record_id_sample": ids[:5],
        "record_id_sha256": hashlib.sha256(
            "\n".join(ids).encode("utf-8")
        ).hexdigest() if ids else None,
        "record_summaries": [
            {
                "id": record["id"],
                "title": record.get("title"),
                "institutions": record.get("institutions", []),
                "formats": record.get("formats", []),
                "online_urls_present": bool(record.get("onlineUrls")),
            }
            for record in records[:3]
        ],
        "building_facet_sample": [
            {"value": x.get("value"), "translated": x.get("translated"),
             "count": x.get("count")}
            for x in building[:20] if isinstance(x, dict)
        ],
        "building_facet_total_entries": len(building),
        "kavi_building_candidates": _kavi_building_candidates(building),
    }


def run_probe(session: requests.Session | None = None) -> dict[str, Any]:
    if session is None:
        session = requests.Session()
        session.headers.update({
            **HEADERS,
            "User-Agent": f"{USER_AGENT}/1.0 (+public-catalogue-metadata-probe)",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.3",
        })
    guard = Guard(session)
    report: dict[str, Any] = {
        "version": VERSION,
        "analysis_number": 82,
        "institution": "KAVI - National Audiovisual Institute",
        "robots": guard.evidence, "surfaces": [], "api_probes": [],
        "staged_collector_authorized": False,
        "individual_film_records_enumerated": 0,
        "complete_kavi_catalogue": False,
        "gate_assessment": "hold_unverified_access",
        "notes": [
            "Elonet is a KAVI catalogue and VOD service, not automatically proof"
            " of custody or licensed reuse for each indexed film",
            "Finna metadata CC0 does not extend to video, images or media rights",
            "Only bounded API requests; no resumptionToken issued until"
            " a documented KAVI-specific scope is verified",
        ],
    }
    for label, url in SURFACES:
        result = guard.get(url)
        row: dict[str, Any] = {
            "surface": label, "requested_url": url,
            "final_url": result.final, "status": result.status,
            "error": result.error,
        }
        if not result.error and "html" in result.mime.lower():
            row.update(parse_public_page(result.text, result.final or url))
        report["surfaces"].append(row)
    for label, url, facet in (
        ("building_facet", FACET_QUERY, True),
        ("documented_title_sample", SAMPLE_QUERY, False),
    ):
        result = guard.get(url)
        row = {
            "probe": label, "requested_url": url, "final_url": result.final,
            "status": result.status, "error": result.error,
        }
        if not result.error and "json" in result.mime.lower():
            try:
                row.update(parse_finna_response(result.text, expect_facets=facet))
            except ValueError as ex:
                row["error"] = str(ex)
        elif not result.error:
            row["error"] = "api_non_json_content"
        report["api_probes"].append(row)
    # Only the live API facet, never a hardcoded or inferred provider ID,
    # can authorize a limited, read-only provider-filtered sample.
    facet_row = next(
        (r for r in report["api_probes"] if r["probe"] == "building_facet"),
        None,
    )
    if facet_row is not None and not facet_row["error"]:
        matches = facet_row.get("kavi_building_candidates", [])
        report["kavi_facet_resolution"] = (
            "one_facet_candidate" if len(matches) == 1
            else "none" if not matches else "ambiguous_multiple"
        )
        if len(matches) == 1:
            filter_url = _build_verified_facet_query(matches[0]["value"])
            result = guard.get(filter_url)
            filtered: dict[str, Any] = {
                "probe": "verified_building_facet_sample",
                "requested_url": filter_url,
                "final_url": result.final, "status": result.status,
                "error": result.error,
                "verified_building": matches[0],
            }
            if not result.error and "json" in result.mime.lower():
                try:
                    filtered.update(parse_finna_response(result.text))
                except ValueError as ex:
                    filtered["error"] = str(ex)
            elif not result.error:
                filtered["error"] = "api_non_json_content"
            report["api_probes"].append(filtered)
            title_row = next(
                (r for r in report["api_probes"]
                 if r["probe"] == "documented_title_sample"), None,
            )
            video_codes = _video_format_candidates(
                title_row.get("record_summaries", [])
                if title_row is not None and not title_row["error"] else [],
            )
            report["observed_video_format_codes"] = video_codes
            if len(video_codes) == 1:
                video_url = _build_verified_video_query(
                    matches[0]["value"], video_codes[0],
                )
                video_response = guard.get(video_url)
                video_row: dict[str, Any] = {
                    "probe": "verified_building_and_video_sample",
                    "requested_url": video_url,
                    "final_url": video_response.final,
                    "status": video_response.status,
                    "error": video_response.error,
                    "verified_building": matches[0],
                    "verified_video_format": video_codes[0],
                }
                if not video_response.error and "json" in video_response.mime.lower():
                    try:
                        video_row.update(parse_finna_response(video_response.text))
                    except ValueError as ex:
                        video_row["error"] = str(ex)
                elif not video_response.error:
                    video_row["error"] = "api_non_json_content"
                report["api_probes"].append(video_row)
    if any(row["error"] for row in report["api_probes"]):
        report["gate_assessment"] = "hold_finna_api_unverifiable"
    elif any(row["error"] for row in report["surfaces"]):
        report["gate_assessment"] = "hold_required_surface_unverifiable"
    else:
        report["gate_assessment"] = "investigate_kavi_provider_scope_and_batch_enumeration"
    # This introductory probe NEVER promotes a stage, even if API metadata is reachable.
    return report


def dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
