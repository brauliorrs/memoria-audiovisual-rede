import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    MURNAU_STIFTUNG_FILM_SEARCH_URL,
    MURNAU_STIFTUNG_HOME_URL,
    MURNAU_STIFTUNG_MOVIE_SEARCH_URL,
    MURNAU_STIFTUNG_MOVIE_URL_TEMPLATE,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


MURNAU_STIFTUNG_REPOSITORY_CODE = "DE-FWMS"
MURNAU_STIFTUNG_ARCHIVE_TYPE = "Public film archive and rights-holding foundation"
MURNAU_STIFTUNG_COUNTRY = normalize_country("Germany")
MURNAU_STIFTUNG_INSTITUTION_NAME = "Friedrich-Wilhelm-Murnau-Stiftung"
MURNAU_STIFTUNG_PLATFORM_LABEL = "Filmsuche der Murnau-Stiftung"
MURNAU_STIFTUNG_YEAR_START = 1890
MURNAU_STIFTUNG_YEAR_END = 1969
MURNAU_STIFTUNG_MAX_DETAIL_PAGES = 30

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"})


def _clean(value, limit=None):
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
    return parser.can_fetch(SESSION.headers.get("User-Agent", "*"), url), "robots_evaluated"


def parse_murnau_search_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = _clean(soup.get_text(" ", strip=True))
    count_match = re.search(r"([\d\s\.]+)\s+Suchergebnisse", text, re.I)
    declared_count = int(re.sub(r"\D", "", count_match.group(1))) if count_match else 0
    records = []
    seen = set()
    for anchor in soup.find_all("a", href=re.compile(r"^/movie/\d+|https?://[^/]+/movie/\d+", re.I)):
        href = urljoin(page_url, anchor.get("href", ""))
        match = re.search(r"/movie/(\d+)", href)
        if not match:
            continue
        record_id = match.group(1)
        if record_id in seen:
            continue
        seen.add(record_id)
        title = _clean(anchor.get_text(" ", strip=True), 300)
        records.append({
            "record_id": record_id,
            "page_url": href,
            "title": title,
        })
    return declared_count, records


def parse_murnau_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = _clean(soup.get_text(" ", strip=True), 7000)
    heading = soup.find("h2") or soup.find("h1")
    title = _clean(heading.get_text(" ", strip=True) if heading else "", 300)
    record_match = re.search(r"/movie/(\d+)", page_url)
    record_id = record_match.group(1) if record_match else ""
    year_match = re.search(r"\b(?:Jahre|aus dem Jahre)\s+(18\d{2}|19\d{2}|20\d{2})\b", text, re.I)
    if not year_match:
        year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    director_match = re.search(r"\bRegie:\s*([^|]{2,180}?)(?=\s+(?:Drehbuch:|Autor:|Kamera:|Musik:|Bauten:|Kurzinhalt:|Produktion:|$))", text, re.I)
    country_match = re.search(r"\bLand:\s*([^|]{2,80}?)(?=\s+(?:Regie:|Drehbuch:|Autor:|$))", text, re.I)
    length_match = re.search(r"\bLänge:\s*([^|]{2,80}?)(?=\s+(?:Land:|Regie:|$))", text, re.I)
    description = _clean(
        " | ".join(
            item for item in [
                "Ficha pública do catálogo Filmsuche da Murnau-Stiftung.",
                f"Regie: {_clean(director_match.group(1), 180)}" if director_match else "",
                f"Land: {_clean(country_match.group(1), 80)}" if country_match else "",
                f"Länge: {_clean(length_match.group(1), 80)}" if length_match else "",
                text,
            ] if item
        ),
        2200,
    )
    return {
        "record_id": record_id,
        "page_url": page_url,
        "video_link": page_url,
        "platform": MURNAU_STIFTUNG_PLATFORM_LABEL,
        "title": title,
        "subject": _clean(director_match.group(1), 180) if director_match else "",
        "description": description,
        "date": year_match.group(1) if year_match else "",
        "embedded": False,
    }


def collect_murnau_stiftung_institutions():
    return [{
        "institution": MURNAU_STIFTUNG_INSTITUTION_NAME,
        "slug": slugify(MURNAU_STIFTUNG_INSTITUTION_NAME),
        "country": MURNAU_STIFTUNG_COUNTRY,
        "continent": country_to_continent(MURNAU_STIFTUNG_COUNTRY),
        "repository_code": MURNAU_STIFTUNG_REPOSITORY_CODE,
        "archive_type": MURNAU_STIFTUNG_ARCHIVE_TYPE,
        "murnau_stiftung_detail_url": MURNAU_STIFTUNG_FILM_SEARCH_URL,
        "external_url": MURNAU_STIFTUNG_HOME_URL,
        "website_available": True,
        "content_available_in_source": True,
    }]


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": MURNAU_STIFTUNG_REPOSITORY_CODE,
        "archive_type": MURNAU_STIFTUNG_ARCHIVE_TYPE,
        "murnau_stiftung_detail_url": MURNAU_STIFTUNG_FILM_SEARCH_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal(institution, url, status, http_code="", count=0, warning="", error=""):
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


def _video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": MURNAU_STIFTUNG_HOME_URL,
        "platform": MURNAU_STIFTUNG_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description")
        or f"Registro público da Filmsuche; ano de partição: {record.get('date', '')}.",
        "video_published_at": record.get("date", ""),
    }


def collect_murnau_stiftung_dataset():
    institutions = collect_murnau_stiftung_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_id = {}
    year_counts = {}

    allowed, robots_status = _robots_allowed(MURNAU_STIFTUNG_MOVIE_SEARCH_URL)
    if not allowed:
        internal_pages.append(_internal(
            institution,
            MURNAU_STIFTUNG_MOVIE_SEARCH_URL,
            "bloqueado_robots",
            warning="Busca pública por ano.",
            error=robots_status,
        ))
        return institutions, [{
            **_base_row(institution),
            "partner_site": MURNAU_STIFTUNG_HOME_URL,
            "partner_domain": normalize_domain(MURNAU_STIFTUNG_HOME_URL),
            "status": "bloqueado_robots",
            "http_code": "",
            "integrity_status": "sem_registros",
            "final_url": MURNAU_STIFTUNG_MOVIE_SEARCH_URL,
            "video_links_found_total": 0,
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": 1,
            "priority_review": False,
            "warning": f"Coleta bloqueada de forma fail-closed: {robots_status}.",
            "error": robots_status,
        }], [], internal_pages

    for year in range(MURNAU_STIFTUNG_YEAR_START, MURNAU_STIFTUNG_YEAR_END + 1):
        url = f"{MURNAU_STIFTUNG_MOVIE_SEARCH_URL}?year={year}"
        try:
            response = _fetch(url)
            response.raise_for_status()
            declared, rows = parse_murnau_search_page(response.text, response.url)
            year_counts[str(year)] = {"declared": declared, "materialized": len(rows)}
            for row in rows:
                row["date"] = str(year)
                records_by_id.setdefault(row["record_id"], row)
            internal_pages.append(_internal(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(rows),
                warning=f"Partição anual da Filmsuche; robots={robots_status}.",
            ))
        except Exception as exc:
            errors.append(f"{year}: {exc}")
            internal_pages.append(_internal(
                institution,
                url,
                "erro",
                warning="Falha na partição anual.",
                error=str(exc),
            ))

    detail_ids = sorted(records_by_id, key=lambda value: int(value))[:MURNAU_STIFTUNG_MAX_DETAIL_PAGES]
    for record_id in detail_ids:
        url = MURNAU_STIFTUNG_MOVIE_URL_TEMPLATE.format(record_id=record_id)
        try:
            response = _fetch(url)
            response.raise_for_status()
            parsed = parse_murnau_detail_page(response.text, response.url)
            original_year = records_by_id[record_id].get("date", "")
            records_by_id[record_id].update(parsed)
            if not records_by_id[record_id].get("date"):
                records_by_id[record_id]["date"] = original_year
            internal_pages.append(_internal(
                institution,
                response.url,
                "ok",
                response.status_code,
                1,
                warning=f"Ficha pública de item; robots={robots_status}.",
            ))
        except Exception as exc:
            errors.append(f"movie/{record_id}: {exc}")
            internal_pages.append(_internal(
                institution,
                url,
                "erro",
                warning="Falha ao enriquecer ficha pública.",
                error=str(exc),
            ))

    records = list(records_by_id.values())
    video_links = [_video_row(institution, row) for row in records]
    declared_sum = sum(item["declared"] for item in year_counts.values())
    complete_partitions = sum(
        1 for item in year_counts.values()
        if item["declared"] == item["materialized"]
    )
    summary = [{
        **_base_row(institution),
        "partner_site": MURNAU_STIFTUNG_HOME_URL,
        "partner_domain": normalize_domain(MURNAU_STIFTUNG_HOME_URL),
        "status": "ok" if records else "sem_registros",
        "http_code": 200 if records else "",
        "integrity_status": "integro" if records else "sem_registros",
        "final_url": MURNAU_STIFTUNG_FILM_SEARCH_URL,
        "video_links_found_total": len(video_links),
        "embedded_video_signals_total": 0,
        "candidate_internal_pages": len(internal_pages),
        "priority_review": False,
        "warning": _clean(
            "Enumeração determinística por ano (1890–1969) da Filmsuche pública, "
            f"deduplicada por /movie/<id>. Soma declarada nas partições: {declared_sum}; "
            f"IDs únicos materializados: {len(records)}; partições com contagem coincidente: "
            f"{complete_partitions}/{len(year_counts)}. Até {MURNAU_STIFTUNG_MAX_DETAIL_PAGES} "
            "fichas são enriquecidas. A rodada não presume cobertura integral do acervo físico "
            "ou do estoque fiduciário de aproximadamente 20.000 títulos."
        ),
        "error": " | ".join(errors[:10]),
    }]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "MURNAU_STIFTUNG_INSTITUTION_NAME",
    "MURNAU_STIFTUNG_MAX_DETAIL_PAGES",
    "MURNAU_STIFTUNG_PLATFORM_LABEL",
    "MURNAU_STIFTUNG_YEAR_END",
    "MURNAU_STIFTUNG_YEAR_START",
    "collect_murnau_stiftung_dataset",
    "collect_murnau_stiftung_institutions",
    "parse_murnau_detail_page",
    "parse_murnau_search_page",
]
