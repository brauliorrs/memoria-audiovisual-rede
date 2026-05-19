import re
import time
from urllib.parse import parse_qs, quote, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    PPA_HOME_URL,
    PPA_SEARCH_URL_TEMPLATE,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
)
from .crawler import normalize_domain
from .european_aggregators import parse_result_count
from .geography import country_to_continent, normalize_country


PPA_REPOSITORY_CODE = "PT-PPA"
PPA_ARCHIVE_TYPE = "National archival aggregator"
PPA_COUNTRY = normalize_country("Portugal")
PPA_INSTITUTION_NAME = "Portal Português de Arquivos"
PPA_PLATFORM_LABEL = "Portal Português de Arquivos"
PPA_SLUG = "portal-portugues-arquivos"
PPA_QUERY_TERMS = ("audiovisual", "video", "vídeo", "filme", "sonoro")
PPA_MAX_RECORDS_PER_TERM = 25

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_ppa_institutions():
    return [
        {
            "institution": PPA_INSTITUTION_NAME,
            "slug": PPA_SLUG,
            "country": PPA_COUNTRY,
            "continent": country_to_continent(PPA_COUNTRY),
            "repository_code": PPA_REPOSITORY_CODE,
            "archive_type": PPA_ARCHIVE_TYPE,
            "ppa_detail_url": PPA_HOME_URL,
            "external_url": PPA_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _strip_jsession(url):
    return re.sub(r";jsessionid=[^?]+", "", str(url or ""))


def _absolute_ppa_url(url):
    return urljoin(PPA_HOME_URL, _strip_jsession(url))


def _extract_record_id(url):
    parsed = urlparse(_absolute_ppa_url(url))
    values = parse_qs(parsed.query).get("id", [])
    return unquote(values[0]) if values else ""


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _extract_first_url_from_text(text):
    match = re.search(r"https?://[^\s<>\"]+", str(text or ""))
    return match.group(0).rstrip(".,);") if match else ""


def _extract_date_from_text(text):
    match = re.search(r"\bDates?:\s*([0-9][0-9Xx?./\- ]{2,40})", str(text or ""))
    return _clean_text(match.group(1)) if match else ""


def _select_result_records(soup):
    records = soup.select("div.row-fluid.record")
    if records:
        return records
    return [anchor.find_parent(["div", "li", "tr"]) for anchor in soup.select("a[href^='record?id=']")]


def parse_ppa_search_results(html, search_url, query):
    soup = BeautifulSoup(html or "", "html.parser")
    page_text = soup.get_text(" ", strip=True)
    result_count = parse_result_count(page_text)
    records = []
    seen_ids = set()

    for container in _select_result_records(soup):
        if container is None:
            continue
        title_anchor = container.select_one("div.title a[href*='record?id=']") or container.select_one(
            "a[href^='record?id=']"
        )
        if title_anchor is None:
            continue

        record_id = _extract_record_id(title_anchor.get("href", ""))
        title = _clean_text(title_anchor.get_text(" ", strip=True))
        if not record_id or record_id in seen_ids or not title:
            continue

        description_node = container.select_one(".subjects")
        description = _clean_text(
            description_node.get_text(" ", strip=True) if description_node else "",
            limit=500,
        )
        original_anchor = container.select_one(".originalLink a[href]")
        source_anchor = container.select_one(".archiveLink a[href]")
        original_url = _absolute_ppa_url(original_anchor.get("href", "")) if original_anchor else ""
        source_url = _absolute_ppa_url(source_anchor.get("href", "")) if source_anchor else ""
        text_url = _extract_first_url_from_text(description)

        records.append(
            {
                "record_id": record_id,
                "title": title,
                "ppa_url": _absolute_ppa_url(title_anchor.get("href", "")),
                "original_url": original_url,
                "data_source": _clean_text(source_anchor.get_text(" ", strip=True)) if source_anchor else "",
                "data_source_url": source_url,
                "description": description,
                "text_url": text_url,
                "date": _extract_date_from_text(container.get_text(" ", strip=True)),
                "query": query,
                "search_url": search_url,
                "external_source_detected": bool(original_url or text_url),
            }
        )
        seen_ids.add(record_id)
        if len(records) >= PPA_MAX_RECORDS_PER_TERM:
            break
    return records, result_count


def _fetch_search_page(query):
    search_url = PPA_SEARCH_URL_TEMPLATE.format(query=quote(query))
    response = SESSION.get(search_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    return response, search_url


def collect_ppa_dataset():
    institutions = collect_ppa_institutions()
    institution = institutions[0]
    discovered_records = {}
    internal_pages = []
    search_result_total = 0

    for index, query in enumerate(PPA_QUERY_TERMS):
        if index:
            time.sleep(max(SLEEP_BETWEEN_REQUESTS, 1))
        try:
            response, search_url = _fetch_search_page(query)
            records, result_count = [], 0
            status = "ok" if response.status_code < 400 else "erro"
            error = ""
            if response.status_code == 200:
                records, result_count = parse_ppa_search_results(response.text, response.url, query)
                search_result_total += result_count
                for record in records:
                    discovered_records.setdefault(record["record_id"], record)
            else:
                error = f"HTTP {response.status_code}"

            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": PPA_HOME_URL,
                    "internal_page": response.url if response is not None else search_url,
                    "status": status,
                    "http_code": response.status_code if response is not None else "",
                    "video_links_found": len(records),
                    "embedded_signals": sum(1 for record in records if record["external_source_detected"]),
                    "warning": f"Busca pública no PPA pelo termo: {query}.",
                    "error": error,
                }
            )
        except Exception as error:
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": PPA_HOME_URL,
                    "internal_page": PPA_SEARCH_URL_TEMPLATE.format(query=quote(query)),
                    "status": "erro",
                    "http_code": "",
                    "video_links_found": 0,
                    "embedded_signals": 0,
                    "warning": "",
                    "error": str(error),
                }
            )

    video_links = [_record_to_video_row(institution, record) for record in discovered_records.values()]
    external_signals = sum(1 for record in discovered_records.values() if record["external_source_detected"])
    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus incorporado após validação total da busca pública do PPA; os registros indicam "
        "evidência audiovisual em metadados ou descrições, não reprodução audiovisual garantida."
    )

    summary = [
        {
            **_base_row(institution),
            "partner_site": PPA_HOME_URL,
            "partner_domain": normalize_domain(PPA_HOME_URL),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "restrito",
            "final_url": PPA_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": external_signals,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "alta" if not video_links else "media",
            "warning": f"{summary_warning} Resultados brutos sinalizados pela busca: {search_result_total}.",
            "error": summary_error,
        }
    ]
    return institutions, summary, video_links, internal_pages


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": PPA_REPOSITORY_CODE,
        "archive_type": PPA_ARCHIVE_TYPE,
        "ppa_detail_url": PPA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _record_to_video_row(institution, record):
    access_note = (
        "registro descritivo com ligação à fonte original detectada"
        if record.get("external_source_detected")
        else "registro descritivo recuperado"
    )
    source_note = f"; fonte agregada: {record.get('data_source')}" if record.get("data_source") else ""
    original_note = f"; registro original: {record.get('original_url')}" if record.get("original_url") else ""
    text_url_note = f"; URL textual: {record.get('text_url')}" if record.get("text_url") else ""
    description_note = f"; descrição: {record.get('description')}" if record.get("description") else ""
    return {
        **_base_row(institution),
        "partner_site": record.get("data_source") or PPA_PLATFORM_LABEL,
        "platform": PPA_PLATFORM_LABEL,
        "video_link": record.get("ppa_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("query", ""),
        "video_description": _clean_text(
            f"{access_note}; registro PPA {record.get('record_id', '')}"
            f"{source_note}{original_note}{text_url_note}{description_note}",
            limit=900,
        ),
        "video_published_at": record.get("date", ""),
    }


__all__ = [
    "PPA_QUERY_TERMS",
    "_extract_record_id",
    "collect_ppa_dataset",
    "collect_ppa_institutions",
    "parse_ppa_search_results",
]
