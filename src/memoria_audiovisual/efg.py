import re
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    EUROPEAN_FILM_GATEWAY_HOME_URL,
    EUROPEAN_FILM_GATEWAY_SEARCH_URL_TEMPLATE,
    HEADERS,
)
from .crawler import normalize_domain, slugify


EFG_REPOSITORY_CODE = "EU-EFG"
EFG_ARCHIVE_TYPE = "European film and audiovisual aggregator"
EFG_COUNTRY_SCOPE = "Europa"
EFG_CONTINENT = "Europe"
EFG_QUERY_TERMS = ("film", "video")
EFG_MAX_RECORDS_PER_PAGE = 25
EFG_REQUEST_TIMEOUT = 12

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_european_film_gateway_institutions():
    institution_name = "European Film Gateway"
    return [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "country": EFG_COUNTRY_SCOPE,
            "continent": EFG_CONTINENT,
            "repository_code": EFG_REPOSITORY_CODE,
            "archive_type": EFG_ARCHIVE_TYPE,
            "efg_detail_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
            "external_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _looks_like_navigation(title, href):
    lowered_title = title.lower()
    lowered_href = str(href or "").lower()
    navigation_terms = {
        "about",
        "collections",
        "contact",
        "details",
        "faq",
        "imprint",
        "news",
        "privacy policy",
        "terms of use",
    }
    if lowered_title in navigation_terms:
        return True
    return lowered_href.startswith("#") or lowered_href.startswith("mailto:")


def _anchor_context(anchor):
    fragments = []
    node = anchor
    for _ in range(4):
        if node is None:
            break
        fragments.append(node.get_text(" ", strip=True))
        node = node.parent
    return _clean_text(" ".join(fragments))


def _extract_efg_item_id(url):
    path = str(url or "").rstrip("/").split("?")[0]
    return path.rsplit("/", 1)[-1] if "/" in path else path


def parse_efg_video_items(html, page_url, query=""):
    soup = BeautifulSoup(html or "", "html.parser")
    records = []
    seen_urls = set()
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not href or not title or _looks_like_navigation(title, href):
            continue

        absolute_url = urljoin(page_url, href.split(";jsessionid=", 1)[0])
        context = _anchor_context(anchor)
        if "video |" not in context.lower() and " video " not in f" {context.lower()} ":
            continue
        if absolute_url in seen_urls:
            continue

        records.append(
            {
                "record_id": _extract_efg_item_id(absolute_url),
                "title": title,
                "item_url": absolute_url,
                "query": query,
                "provider": "European Film Gateway",
                "description": "registro de vídeo detectado na superfície pública do European Film Gateway",
            }
        )
        seen_urls.add(absolute_url)
        if len(records) >= EFG_MAX_RECORDS_PER_PAGE:
            break
    return records


def _fetch_page(url):
    response = SESSION.get(
        url,
        timeout=EFG_REQUEST_TIMEOUT,
        allow_redirects=True,
    )
    return response


def collect_european_film_gateway_dataset():
    institutions = collect_european_film_gateway_institutions()
    institution = institutions[0]
    slug = institution["slug"]
    country = institution["country"]
    continent = institution["continent"]
    external_url = institution["external_url"]

    seed_pages = [("home", EUROPEAN_FILM_GATEWAY_HOME_URL)]
    for query in EFG_QUERY_TERMS:
        seed_pages.append(
            (
                query,
                EUROPEAN_FILM_GATEWAY_SEARCH_URL_TEMPLATE.format(query=quote(query)),
            )
        )

    discovered_records = {}
    internal_pages = []

    for query, seed_url in seed_pages:
        try:
            response = _fetch_page(seed_url)
            status = "ok" if response.status_code < 400 else "erro"
            records = []
            warning = ""
            error = ""
            if response.status_code == 200:
                records = parse_efg_video_items(response.text, response.url, query=query)
                for record in records:
                    discovered_records.setdefault(record["item_url"], record)
                warning = (
                    "Página semeada para observar o agregador europeu especializado em cinema."
                )
            else:
                error = f"HTTP {response.status_code}"

            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": country,
                    "continent": continent,
                    "repository_code": EFG_REPOSITORY_CODE,
                    "archive_type": EFG_ARCHIVE_TYPE,
                    "efg_detail_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
                    "content_available_in_source": bool(records),
                    "website_available": response.status_code == 200,
                    "partner_site": external_url,
                    "internal_page": response.url,
                    "status": status,
                    "http_code": response.status_code,
                    "video_links_found": len(records),
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
                    "country": country,
                    "continent": continent,
                    "repository_code": EFG_REPOSITORY_CODE,
                    "archive_type": EFG_ARCHIVE_TYPE,
                    "efg_detail_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
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
        video_links.append(
            {
                "institution": institution["institution"],
                "slug": slug,
                "country": country,
                "continent": continent,
                "repository_code": EFG_REPOSITORY_CODE,
                "archive_type": EFG_ARCHIVE_TYPE,
                "efg_detail_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
                "content_available_in_source": True,
                "website_available": True,
                "partner_site": record.get("provider") or external_url,
                "platform": "European Film Gateway",
                "video_link": record["item_url"],
                "video_title": record.get("title", ""),
                "video_subject": record.get("query", ""),
                "video_description": record.get("description", ""),
                "video_published_at": "",
            }
        )

    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus europeu especializado incorporado com protocolo próprio. Quando a superfície pública "
        "falha ou bloqueia a sondagem simples, isso permanece registrado como instabilidade de acesso, "
        "não como ausência de acervo audiovisual."
    )
    summary = [
        {
            "institution": institution["institution"],
            "slug": slug,
            "country": country,
            "continent": continent,
            "repository_code": EFG_REPOSITORY_CODE,
            "archive_type": EFG_ARCHIVE_TYPE,
            "efg_detail_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
            "content_available_in_source": bool(video_links),
            "website_available": summary_status == "ok",
            "partner_site": external_url,
            "partner_domain": normalize_domain(external_url),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "instavel",
            "final_url": EUROPEAN_FILM_GATEWAY_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "alta" if video_links else "media",
            "warning": summary_warning,
            "error": summary_error,
        }
    ]

    return institutions, summary, video_links, internal_pages


__all__ = [
    "EFG_QUERY_TERMS",
    "collect_european_film_gateway_dataset",
    "collect_european_film_gateway_institutions",
    "parse_efg_video_items",
]
