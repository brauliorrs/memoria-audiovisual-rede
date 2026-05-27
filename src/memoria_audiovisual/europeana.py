import re
import time
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    EUROPEANA_API_REFERENCE_URL,
    EUROPEANA_HOME_URL,
    EUROPEANA_SEARCH_URL_TEMPLATE,
    HEADERS,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
)
from .crawler import normalize_domain, slugify
from .european_aggregators import parse_result_count
from .geography import country_to_continent, normalize_country


EUROPEANA_REPOSITORY_CODE = "EU-EUROPEANA"
EUROPEANA_ARCHIVE_TYPE = "European cultural aggregator with audiovisual records"
EUROPEANA_COUNTRY = normalize_country("Netherlands")
EUROPEANA_QUERY_TERMS = ("video", "audiovisual", "moving image")
EUROPEANA_MAX_RECORDS_PER_TERM = 8
AUDIOVISUAL_TYPE_HINTS = (
    "audiovisual",
    "film",
    "moving image",
    "video",
)

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_europeana_institutions():
    institution_name = "Europeana"
    return [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "country": EUROPEANA_COUNTRY,
            "continent": country_to_continent(EUROPEANA_COUNTRY),
            "repository_code": EUROPEANA_REPOSITORY_CODE,
            "archive_type": EUROPEANA_ARCHIVE_TYPE,
            "europeana_detail_url": EUROPEANA_HOME_URL,
            "external_url": EUROPEANA_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _extract_item_id(url):
    parsed = urlparse(str(url or ""))
    marker = "/item/"
    if marker not in parsed.path:
        return parsed.path.rstrip("/").rsplit("/", 1)[-1]
    return parsed.path.split(marker, 1)[1].strip("/")


def _nearest_card(anchor):
    node = anchor
    for _ in range(6):
        if node is None:
            return anchor
        classes = set(node.get("class", []))
        if "card-wrapper" in classes:
            return node
        node = node.parent
    return anchor.parent or anchor


def parse_europeana_search_results(html, search_url, query):
    soup = BeautifulSoup(html or "", "html.parser")
    page_text = soup.get_text(" ", strip=True)
    result_count = parse_result_count(page_text)
    records = []
    seen_urls = set()

    for anchor in soup.select("a[href*='/en/item/']"):
        href = anchor.get("href", "")
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not href or not title:
            continue

        item_url = urljoin(search_url, href)
        if item_url in seen_urls:
            continue

        card = _nearest_card(anchor)
        card_texts = [
            _clean_text(node.get_text(" ", strip=True))
            for node in card.select(".card-text")
            if _clean_text(node.get_text(" ", strip=True))
        ]
        creator = card_texts[0] if card_texts else ""
        provider = card_texts[-1] if card_texts else ""
        records.append(
            {
                "record_id": _extract_item_id(item_url),
                "title": title,
                "item_url": item_url,
                "query": query,
                "creator": creator,
                "provider": provider,
                "description": _clean_text(" | ".join(card_texts)),
                "search_url": search_url,
            }
        )
        seen_urls.add(item_url)
        if len(records) >= EUROPEANA_MAX_RECORDS_PER_TERM:
            break
    return records, result_count


def _fetch_page(url):
    response = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    return response


def _extract_token_after(tokens, label):
    lowered_label = label.lower()
    for index, token in enumerate(tokens):
        if token.lower() == lowered_label and index + 1 < len(tokens):
            return tokens[index + 1]
    return ""


def _parse_europeana_detail(html):
    soup = BeautifulSoup(html or "", "html.parser")
    tokens = [_clean_text(token) for token in soup.get_text(" | ", strip=True).split("|")]
    tokens = [token for token in tokens if token]
    type_value = _extract_token_after(tokens, "Type of item")
    date_value = _extract_token_after(tokens, "Date")
    provider = _extract_token_after(tokens, "Providing institution")
    country = _extract_token_after(tokens, "Providing country")
    rights = _extract_token_after(tokens, "Rights")
    return {
        "type_value": type_value,
        "date_value": date_value,
        "provider": provider,
        "country": normalize_country(country) if country else "",
        "rights": rights,
    }


def _is_audiovisual_record(record):
    haystack = " ".join(
        [
            record.get("title", ""),
            record.get("type_value", ""),
            record.get("description", ""),
        ]
    ).lower()
    return any(hint in haystack for hint in AUDIOVISUAL_TYPE_HINTS)


def _enrich_records_with_detail(records):
    enriched = []
    for index, record in enumerate(records):
        if index:
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        working = dict(record)
        try:
            response = _fetch_page(record["item_url"])
            if response.status_code == 200:
                detail = _parse_europeana_detail(response.text)
                working.update(detail)
                working["detail_status"] = "ok"
                working["detail_error"] = ""
            else:
                working["detail_status"] = "erro"
                working["detail_error"] = f"HTTP {response.status_code}"
        except Exception as error:
            working["detail_status"] = "erro"
            working["detail_error"] = str(error)

        if _is_audiovisual_record(working):
            enriched.append(working)
    return enriched


def collect_europeana_dataset():
    institutions = collect_europeana_institutions()
    institution = institutions[0]
    slug = institution["slug"]
    external_url = institution["external_url"]

    discovered_records = {}
    internal_pages = []
    search_result_total = 0

    seed_pages = [("home", EUROPEANA_HOME_URL), ("api", EUROPEANA_API_REFERENCE_URL)]
    for query in EUROPEANA_QUERY_TERMS:
        seed_pages.append((query, EUROPEANA_SEARCH_URL_TEMPLATE.format(query=quote(query))))

    for query, seed_url in seed_pages:
        try:
            response = _fetch_page(seed_url)
            status = "ok" if response.status_code < 400 else "erro"
            records = []
            retained_records = []
            result_count = 0
            warning = ""
            error = ""
            if response.status_code == 200 and query not in {"home", "api"}:
                records, result_count = parse_europeana_search_results(response.text, response.url, query)
                search_result_total += result_count
                retained_records = _enrich_records_with_detail(records)
                for record in retained_records:
                    discovered_records.setdefault(record["item_url"], record)
                warning = (
                    "Busca pública da Europeana com filtro de mídia; os registros são triados "
                    "por sinais audiovisuais antes de entrarem no catálogo."
                )
            elif response.status_code == 200:
                warning = "Página semeada para documentar a infraestrutura pública da Europeana."
            else:
                error = f"HTTP {response.status_code}"

            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": institution["country"],
                    "continent": institution["continent"],
                    "repository_code": EUROPEANA_REPOSITORY_CODE,
                    "archive_type": EUROPEANA_ARCHIVE_TYPE,
                    "europeana_detail_url": EUROPEANA_HOME_URL,
                    "content_available_in_source": bool(retained_records),
                    "website_available": response.status_code == 200,
                    "partner_site": external_url,
                    "internal_page": response.url,
                    "status": status,
                    "http_code": response.status_code,
                    "video_links_found": len(retained_records),
                    "embedded_signals": len(records),
                    "warning": warning,
                    "error": error,
                }
            )
        except Exception as error:
            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": institution["country"],
                    "continent": institution["continent"],
                    "repository_code": EUROPEANA_REPOSITORY_CODE,
                    "archive_type": EUROPEANA_ARCHIVE_TYPE,
                    "europeana_detail_url": EUROPEANA_HOME_URL,
                    "content_available_in_source": False,
                    "website_available": False,
                    "partner_site": external_url,
                    "internal_page": seed_url,
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
        record_country = record.get("country") or institution["country"]
        video_links.append(
            {
                "institution": institution["institution"],
                "slug": slug,
                "country": record_country,
                "continent": country_to_continent(record_country),
                "repository_code": EUROPEANA_REPOSITORY_CODE,
                "archive_type": EUROPEANA_ARCHIVE_TYPE,
                "europeana_detail_url": EUROPEANA_HOME_URL,
                "content_available_in_source": True,
                "website_available": True,
                "partner_site": record.get("provider") or external_url,
                "platform": "Europeana",
                "video_link": record["item_url"],
                "video_title": record.get("title", ""),
                "video_subject": record.get("query", ""),
                "video_description": _clean_text(
                    "; ".join(
                        [
                            f"tipo Europeana: {record.get('type_value', '')}",
                            f"provedor: {record.get('provider', '')}",
                            f"direitos: {record.get('rights', '')}",
                        ]
                    )
                ),
                "video_published_at": record.get("date_value", ""),
            }
        )

    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus cultural europeu amplo incorporado com recorte audiovisual. O catálogo não equivale "
        "a um arquivo audiovisual especializado: registra apenas resultados públicos filtrados por mídia "
        "e por sinais audiovisuais."
    )
    summary = [
        {
            "institution": institution["institution"],
            "slug": slug,
            "country": institution["country"],
            "continent": institution["continent"],
            "repository_code": EUROPEANA_REPOSITORY_CODE,
            "archive_type": EUROPEANA_ARCHIVE_TYPE,
            "europeana_detail_url": EUROPEANA_HOME_URL,
            "content_available_in_source": bool(video_links),
            "website_available": summary_status == "ok",
            "partner_site": external_url,
            "partner_domain": normalize_domain(external_url),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "instavel",
            "final_url": EUROPEANA_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": search_result_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "alta" if video_links else "media",
            "warning": summary_warning,
            "error": summary_error,
        }
    ]

    return institutions, summary, video_links, internal_pages


__all__ = [
    "EUROPEANA_QUERY_TERMS",
    "collect_europeana_dataset",
    "collect_europeana_institutions",
    "parse_europeana_search_results",
]
