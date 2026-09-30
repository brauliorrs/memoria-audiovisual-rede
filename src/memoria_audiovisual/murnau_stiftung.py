from __future__ import annotations

import re
import time
from urllib.parse import urlencode, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    MURNAU_STIFTUNG_DETAIL_URL_TEMPLATE,
    MURNAU_STIFTUNG_HOLDINGS_URL,
    MURNAU_STIFTUNG_HOME_URL,
    MURNAU_STIFTUNG_SEARCH_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


MURNAU_STIFTUNG_INSTITUTION_NAME = "Friedrich-Wilhelm-Murnau-Stiftung"
MURNAU_STIFTUNG_REPOSITORY_CODE = "DE-FW-MURNAU-STIFTUNG"
MURNAU_STIFTUNG_ARCHIVE_TYPE = "Film archive and rights-holding foundation with public film database"
MURNAU_STIFTUNG_COUNTRY = normalize_country("Germany")
MURNAU_STIFTUNG_PLATFORM_LABEL = "Murnau-Stiftung Filmsuche"
MURNAU_STIFTUNG_START_YEAR = 1895
MURNAU_STIFTUNG_END_YEAR = 1969

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = None
    for attempt in range(4):
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        if response.status_code not in {429, 503}:
            return response
        time.sleep(1.0 * (attempt + 1))
    return response


def _robots_allowed(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = SESSION.get(robots_url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    except requests.RequestException:
        return False, "robots_unreachable"
    if response.status_code in {404, 410}:
        return True, "robots_absent"
    if response.status_code != 200:
        return False, f"robots_http_{response.status_code}"
    parser = RobotFileParser()
    parser.set_url(response.url)
    parser.parse(response.text.splitlines())
    user_agent = SESSION.headers.get("User-Agent", "*")
    return parser.can_fetch(user_agent, url), "robots_evaluated"


def _record_id_from_url(url):
    match = re.search(r"/movie/(\d+)(?:[/?#]|$)", str(url or ""))
    return match.group(1) if match else ""


def _parse_result_total(text):
    match = re.search(r"([\d.\s\u00a0]+)\s+Suchergebnisse?", str(text or ""), re.I)
    if not match:
        return 0
    return int(re.sub(r"\D", "", match.group(1)) or 0)


def _parse_declared_holdings_total(text):
    normalized = _clean_text(text)
    patterns = (
        r"mehr\s+als\s+([\d.\s\u00a0]+)\s+Stumm-\s*und\s+Tonfilme",
        r"mehr\s+als\s+([\d.\s\u00a0]+)\s+Filme",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized, re.I)
        if match:
            return int(re.sub(r"\D", "", match.group(1)) or 0)
    return 0


def parse_murnau_search_page(html_text, page_url, *, query_year=""):
    soup = BeautifulSoup(html_text or "", "html.parser")
    page_text = _clean_text(soup.get_text(" ", strip=True))
    declared_total = _parse_result_total(page_text)
    records = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        detail_url = urljoin(page_url, anchor.get("href", ""))
        record_id = _record_id_from_url(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        title = _clean_text(anchor.get_text(" ", strip=True), limit=350)
        if not title:
            title = _clean_text(anchor.get("title"), limit=350)
        records.append(
            {
                "record_id": record_id,
                "page_url": MURNAU_STIFTUNG_DETAIL_URL_TEMPLATE.format(record_id=record_id),
                "title": title or f"Film {record_id}",
                "date": str(query_year or "").strip(),
                "source_query_url": page_url,
            }
        )
    return records, declared_total


def parse_murnau_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True), limit=12000)
    heading = soup.find("h1") or soup.find("h2")
    title = _clean_text(heading.get_text(" ", strip=True) if heading else "", limit=350)
    record_id = _record_id_from_url(page_url)
    year_match = re.search(r"(?:Jahre?|aus\s+dem\s+Jahre)\s+(\d{4})(?:\s*[-/]\s*(\d{4}))?", text, re.I)
    if not year_match:
        year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    year = year_match.group(1) if year_match else ""
    director_match = re.search(r"\bRegie:\s*([^•|]+?)(?=\s+(?:Drehbuch:|Autor:|Kamera:|Musik:|Ton:|Bauten:|Produktion:|Kurzinhalt:|$))", text, re.I)
    production_match = re.search(r"\bProduktion:\s*([^•|]+?)(?=\s+(?:FSK-|©|$))", text, re.I)
    length_match = re.search(r"\bLänge:\s*([^•|]+?)(?=\s+(?:Land:|Regie:|$))", text, re.I)
    return {
        "record_id": record_id,
        "page_url": page_url,
        "title": title or f"Film {record_id}",
        "date": year,
        "director": _clean_text(director_match.group(1), limit=300) if director_match else "",
        "production": _clean_text(production_match.group(1), limit=500) if production_match else "",
        "length": _clean_text(length_match.group(1), limit=150) if length_match else "",
    }


def collect_murnau_stiftung_institutions():
    return [
        {
            "institution": MURNAU_STIFTUNG_INSTITUTION_NAME,
            "slug": slugify(MURNAU_STIFTUNG_INSTITUTION_NAME),
            "country": MURNAU_STIFTUNG_COUNTRY,
            "continent": country_to_continent(MURNAU_STIFTUNG_COUNTRY),
            "repository_code": MURNAU_STIFTUNG_REPOSITORY_CODE,
            "archive_type": MURNAU_STIFTUNG_ARCHIVE_TYPE,
            "murnau_stiftung_detail_url": MURNAU_STIFTUNG_HOME_URL,
            "external_url": MURNAU_STIFTUNG_SEARCH_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": MURNAU_STIFTUNG_REPOSITORY_CODE,
        "archive_type": MURNAU_STIFTUNG_ARCHIVE_TYPE,
        "murnau_stiftung_detail_url": MURNAU_STIFTUNG_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": MURNAU_STIFTUNG_HOME_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": count,
        "embedded_signals": 0,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    year = record.get("date", "")
    description = (
        "Registro de filme materializado pela busca pública da Murnau-Stiftung. "
        "O permalink aponta para metadados de catálogo; não implica que o filme esteja "
        "disponível para streaming público. Exibição, consulta e licenciamento seguem "
        "as condições declaradas pela instituição."
    )
    return {
        **_base_row(institution),
        "partner_site": MURNAU_STIFTUNG_HOME_URL,
        "platform": MURNAU_STIFTUNG_PLATFORM_LABEL,
        "video_link": record["page_url"],
        "video_title": record.get("title", ""),
        "video_subject": f"ano de busca: {year}" if year else "catálogo de filmes",
        "video_description": description,
        "video_published_at": year,
    }


def collect_murnau_stiftung_dataset():
    institutions = collect_murnau_stiftung_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_id = {}
    declared_holdings_total = 0
    declared_search_total = 0
    mismatched_partitions = []

    allowed, robots_status = _robots_allowed(MURNAU_STIFTUNG_SEARCH_URL)
    if not allowed:
        internal_pages.append(
            _internal_page_row(
                institution,
                MURNAU_STIFTUNG_SEARCH_URL,
                "bloqueado_robots",
                warning="Filmsuche pública; coleta interrompida antes da busca.",
                error=robots_status,
            )
        )
        summary = [
            {
                **_base_row(institution),
                "partner_site": MURNAU_STIFTUNG_HOME_URL,
                "partner_domain": normalize_domain(MURNAU_STIFTUNG_HOME_URL),
                "status": "sem_registros",
                "http_code": "",
                "integrity_status": "instavel",
                "final_url": MURNAU_STIFTUNG_SEARCH_URL,
                "video_links_found_total": 0,
                "embedded_video_signals_total": 0,
                "candidate_internal_pages": 1,
                "priority_review": True,
                "warning": (
                    "A base Filmsuche foi confirmada publicamente, mas a rodada foi "
                    "interrompida porque a política robots não pôde ser validada."
                ),
                "error": robots_status,
            }
        ]
        return institutions, summary, [], internal_pages

    try:
        response = _fetch(MURNAU_STIFTUNG_HOLDINGS_URL)
        response.raise_for_status()
        declared_holdings_total = _parse_declared_holdings_total(response.text)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                warning=f"Página institucional do acervo; robots={robots_status}.",
            )
        )
    except Exception as error:
        errors.append(f"holdings: {error}")

    for year in range(MURNAU_STIFTUNG_START_YEAR, MURNAU_STIFTUNG_END_YEAR + 1):
        search_url = f"{MURNAU_STIFTUNG_SEARCH_URL}?{urlencode({'year': year})}"
        try:
            response = _fetch(search_url)
            response.raise_for_status()
            records, declared_total = parse_murnau_search_page(
                response.text,
                response.url,
                query_year=str(year),
            )
            declared_search_total += declared_total
            if declared_total != len(records):
                mismatched_partitions.append(
                    {
                        "year": year,
                        "declared": declared_total,
                        "parsed": len(records),
                    }
                )
            for record in records:
                current = records_by_id.get(record["record_id"])
                if current is None:
                    records_by_id[record["record_id"]] = record
                elif not current.get("title") and record.get("title"):
                    records_by_id[record["record_id"]] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    count=len(records),
                    warning=(
                        f"Partição anual {year}; resultados declarados={declared_total}; "
                        f"links únicos na página={len(records)}; robots={robots_status}."
                    ),
                )
            )
        except Exception as error:
            errors.append(f"{year}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    search_url,
                    "erro",
                    warning=f"Falha na partição anual {year}.",
                    error=str(error),
                )
            )

    records = sorted(
        records_by_id.values(),
        key=lambda row: (row.get("date", ""), row.get("title", ""), row["record_id"]),
    )
    links = [_record_to_video_row(institution, record) for record in records]
    integrity = "integro" if records and not errors and not mismatched_partitions else "instavel"
    mismatch_note = (
        "; ".join(
            f"{item['year']}:{item['parsed']}/{item['declared']}"
            for item in mismatched_partitions[:12]
        )
        if mismatched_partitions
        else "nenhuma"
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": MURNAU_STIFTUNG_HOME_URL,
            "partner_domain": normalize_domain(MURNAU_STIFTUNG_HOME_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": integrity,
            "final_url": MURNAU_STIFTUNG_SEARCH_URL,
            "video_links_found_total": len(links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": integrity != "integro",
            "warning": _clean_text(
                "Snapshot sistemático da Filmsuche por ano, de "
                f"{MURNAU_STIFTUNG_START_YEAR} a {MURNAU_STIFTUNG_END_YEAR}. "
                f"A instituição declara mais de {declared_holdings_total or '6.000'} filmes "
                f"em seu acervo; as partições retornaram {declared_search_total} ocorrências "
                f"de busca e {len(links)} IDs únicos. Divergências resultado/link: {mismatch_note}. "
                "A rodada não afirma que registros sem ano sejam cobertos, nem que o acervo "
                "físico total esteja online. Os permalinks são fichas de metadados, não players."
            ),
            "error": " | ".join(errors[:12]),
        }
    ]
    return institutions, summary, links, internal_pages


__all__ = [
    "MURNAU_STIFTUNG_END_YEAR",
    "MURNAU_STIFTUNG_START_YEAR",
    "collect_murnau_stiftung_dataset",
    "collect_murnau_stiftung_institutions",
    "parse_murnau_detail_page",
    "parse_murnau_search_page",
]
