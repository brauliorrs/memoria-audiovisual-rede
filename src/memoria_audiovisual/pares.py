import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    PARES_HOME_URL,
    PARES_SEARCH_URL_TEMPLATE,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
)
from .crawler import normalize_domain, slugify
from .european_aggregators import parse_result_count
from .geography import country_to_continent, normalize_country


PARES_REPOSITORY_CODE = "ES-PARES"
PARES_ARCHIVE_TYPE = "National archival aggregator"
PARES_COUNTRY = normalize_country("Spain")
PARES_QUERY_TERMS = ("audiovisual", "film", "video", "sonoro")
PARES_MAX_RECORDS_PER_TERM = 25

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_pares_institutions():
    institution_name = "PARES"
    return [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "country": PARES_COUNTRY,
            "continent": country_to_continent(PARES_COUNTRY),
            "repository_code": PARES_REPOSITORY_CODE,
            "archive_type": PARES_ARCHIVE_TYPE,
            "pares_detail_url": PARES_HOME_URL,
            "external_url": PARES_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _extract_record_id(url):
    match = re.search(r"/catalogo/(?:description|show)/(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _clean_result_title(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _absolute_pares_url(url):
    return urljoin("https://pares.mcu.es", str(url or ""))


def parse_pares_search_results(html, search_url, query):
    soup = BeautifulSoup(html or "", "html.parser")
    page_text = soup.get_text(" ", strip=True)
    result_count = parse_result_count(page_text)
    show_links = {}
    for anchor in soup.select("a[href*='/catalogo/show/']"):
        href = anchor.get("href", "")
        record_id = _extract_record_id(href)
        if record_id:
            show_links[record_id] = _absolute_pares_url(href.split(";jsessionid=", 1)[0])

    records = []
    seen_ids = set()
    for anchor in soup.select("a[href*='/catalogo/description/']"):
        href = anchor.get("href", "")
        record_id = _extract_record_id(href)
        title = _clean_result_title(anchor.get_text(" ", strip=True))
        if not record_id or record_id in seen_ids or not title:
            continue
        description_url = _absolute_pares_url(href.split(";jsessionid=", 1)[0])
        show_url = show_links.get(record_id, "")
        records.append(
            {
                "record_id": record_id,
                "title": title,
                "description_url": description_url,
                "show_url": show_url,
                "query": query,
                "search_url": search_url,
                "digital_object_detected": bool(show_url),
            }
        )
        seen_ids.add(record_id)
        if len(records) >= PARES_MAX_RECORDS_PER_TERM:
            break
    return records, result_count


def _fetch_search_page(query):
    search_url = PARES_SEARCH_URL_TEMPLATE.format(query=quote(query))
    response = SESSION.get(search_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    return response, search_url


def collect_pares_dataset():
    institutions = collect_pares_institutions()
    institution = institutions[0]
    slug = institution["slug"]
    country = institution["country"]
    continent = institution["continent"]
    external_url = institution["external_url"]

    discovered_records = {}
    internal_pages = []
    search_result_total = 0
    embedded_signals = 0

    for index, query in enumerate(PARES_QUERY_TERMS):
        if index:
            time.sleep(max(SLEEP_BETWEEN_REQUESTS, 3))
        try:
            response, search_url = _fetch_search_page(query)
            status = "ok" if response.status_code < 400 else "erro"
            records = []
            result_count = 0
            warning = ""
            error = ""
            if response.status_code == 200:
                records, result_count = parse_pares_search_results(response.text, response.url, query)
                search_result_total += result_count
                embedded_signals += sum(1 for record in records if record["digital_object_detected"])
                for record in records:
                    discovered_records.setdefault(record["record_id"], record)
            elif response.status_code == 429:
                warning = "O PARES limitou a taxa de requisições durante a sondagem."
                error = "HTTP 429 Too Many Requests"
            else:
                error = f"HTTP {response.status_code}"

            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": country,
                    "continent": continent,
                    "repository_code": PARES_REPOSITORY_CODE,
                    "archive_type": PARES_ARCHIVE_TYPE,
                    "pares_detail_url": PARES_HOME_URL,
                    "content_available_in_source": bool(records),
                    "website_available": response.status_code == 200 if response is not None else False,
                    "partner_site": external_url,
                    "internal_page": response.url if response is not None else search_url,
                    "status": status,
                    "http_code": response.status_code if response is not None else "",
                    "video_links_found": len(records),
                    "embedded_signals": sum(1 for record in records if record["digital_object_detected"]),
                    "warning": warning or f"Busca pública no PARES pelo termo: {query}.",
                    "error": error,
                }
            )
        except Exception as error:
            search_url = PARES_SEARCH_URL_TEMPLATE.format(query=quote(query))
            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": country,
                    "continent": continent,
                    "repository_code": PARES_REPOSITORY_CODE,
                    "archive_type": PARES_ARCHIVE_TYPE,
                    "pares_detail_url": PARES_HOME_URL,
                    "content_available_in_source": False,
                    "website_available": False,
                    "partner_site": external_url,
                    "internal_page": search_url,
                    "status": "erro",
                    "http_code": "",
                    "video_links_found": 0,
                    "embedded_signals": 0,
                    "warning": "",
                    "error": str(error),
                }
            )

    video_links = []
    for record in discovered_records.values():
        link_url = record.get("show_url") or record["description_url"]
        access_note = "objeto digital detectado" if record.get("show_url") else "registro descritivo recuperado"
        video_links.append(
            {
                "institution": institution["institution"],
                "slug": slug,
                "country": country,
                "continent": continent,
                "repository_code": PARES_REPOSITORY_CODE,
                "archive_type": PARES_ARCHIVE_TYPE,
                "pares_detail_url": PARES_HOME_URL,
                "content_available_in_source": True,
                "website_available": True,
                "partner_site": "PARES",
                "platform": "PARES",
                "video_link": link_url,
                "video_title": record.get("title", ""),
                "video_subject": record.get("query", ""),
                "video_description": f"{access_note}; registro PARES {record.get('record_id', '')}",
                "video_published_at": "",
            }
        )

    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus experimental baseado na primeira página de resultados por termo; "
        "resultados de busca indicam evidência pública detectável, não reprodução audiovisual garantida."
    )
    summary = [
        {
            "institution": institution["institution"],
            "slug": slug,
            "country": country,
            "continent": continent,
            "repository_code": PARES_REPOSITORY_CODE,
            "archive_type": PARES_ARCHIVE_TYPE,
            "pares_detail_url": PARES_HOME_URL,
            "content_available_in_source": bool(video_links),
            "website_available": summary_status == "ok",
            "partner_site": external_url,
            "partner_domain": normalize_domain(external_url),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "restrito",
            "final_url": PARES_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_signals,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "alta" if video_links else "media",
            "warning": summary_warning,
            "error": summary_error,
        }
    ]

    return institutions, summary, video_links, internal_pages


__all__ = [
    "PARES_QUERY_TERMS",
    "collect_pares_dataset",
    "collect_pares_institutions",
    "parse_pares_search_results",
]
