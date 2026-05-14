import re
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

from .config import (
    EUSCREEN_ABOUT_URL,
    EUSCREEN_COLLECTION_GRID_URL_TEMPLATE,
    EUSCREEN_COLLECTIONS_URL,
    EUSCREEN_EUROPEANA_URL,
    EUSCREEN_HOME_URL,
    EUSCREEN_ITEM_URL_TEMPLATE,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import clean_url, normalize_domain, slugify
from .geography import country_to_continent, normalize_country


EUSCREEN_REPOSITORY_CODE = "EU-EUSCREEN"
EUSCREEN_ARCHIVE_TYPE = "European audiovisual aggregator"
EUSCREEN_COUNTRY = normalize_country("Netherlands")
EUSCREEN_GRID_INDEXES = range(1, 7)

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_euscreen_institutions():
    institution_name = "EUscreen"
    return [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "country": EUSCREEN_COUNTRY,
            "continent": country_to_continent(EUSCREEN_COUNTRY),
            "repository_code": EUSCREEN_REPOSITORY_CODE,
            "archive_type": EUSCREEN_ARCHIVE_TYPE,
            "euscreen_detail_url": EUSCREEN_ABOUT_URL,
            "external_url": EUSCREEN_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _extract_item_id(url):
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    item_ids = query.get("item_id") or query.get("id") or []
    if item_ids:
        return item_ids[0].strip()
    match = re.search(r"item\.html\?id=([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else ""


def _parse_item_text(raw_text):
    text = re.sub(r"\s+", " ", raw_text or "").strip()
    if not text:
        return "", "", ""

    provider_match = re.search(r"\bProvider:\s*", text, flags=re.IGNORECASE)
    if not provider_match:
        return text, "", ""

    title = text[: provider_match.start()].strip()
    remainder = text[provider_match.end() :].strip()
    provider = remainder
    description = ""

    return title, provider, description


def _parse_item_parts(parts):
    normalized_parts = [
        re.sub(r"\s+", " ", str(part)).strip()
        for part in parts
        if str(part).strip()
    ]
    if not normalized_parts:
        return "", "", ""

    title = normalized_parts[0]
    provider = ""
    description = ""
    provider_index = None

    for index, part in enumerate(normalized_parts[1:], start=1):
        if part.lower().startswith("provider:"):
            provider_index = index
            provider = part.split(":", 1)[1].strip()
            break

    if provider_index is None:
        return _parse_item_text(" ".join(normalized_parts))

    description = " ".join(normalized_parts[provider_index + 1 :]).strip()
    return title, provider, description


def _fetch_grid_items(grid_url):
    response = SESSION.get(grid_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    items = []
    for anchor in soup.select("a[href*='item_id=']"):
        item_url = clean_url(anchor.get("href", ""))
        item_id = _extract_item_id(item_url)
        if not item_id:
            continue
        title, provider, description = _parse_item_parts(anchor.stripped_strings)
        canonical_url = EUSCREEN_ITEM_URL_TEMPLATE.format(item_id=item_id)
        items.append(
            {
                "item_id": item_id,
                "item_url": canonical_url,
                "title": title or item_id,
                "provider": provider,
                "description": description,
            }
        )
    return items, response.url


def collect_euscreen_dataset():
    institutions = collect_euscreen_institutions()
    institution = institutions[0]
    slug = institution["slug"]
    country = institution["country"]
    continent = institution["continent"]
    external_url = institution["external_url"]

    discovered_items = {}
    internal_pages = []
    embedded_signals = 0

    seed_pages = [
        EUSCREEN_HOME_URL,
        EUSCREEN_COLLECTIONS_URL,
        EUSCREEN_EUROPEANA_URL,
    ]
    for index in EUSCREEN_GRID_INDEXES:
        seed_pages.append(EUSCREEN_COLLECTION_GRID_URL_TEMPLATE.format(index=index))

    for seed_url in seed_pages:
        try:
            if "collection-grid-" in seed_url:
                items, final_url = _fetch_grid_items(seed_url)
            else:
                response = SESSION.get(seed_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
                response.raise_for_status()
                final_url = response.url
                items = []
            embedded_signals += len(items)
            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": country,
                    "continent": continent,
                    "partner_site": external_url,
                    "internal_page": final_url,
                    "status": "ok",
                    "http_code": 200,
                    "video_links_found": len(items),
                    "embedded_signals": len(items),
                    "warning": "Página semeada para observar o agregador audiovisual europeu.",
                    "error": "",
                }
            )
            for item in items:
                discovered_items[item["item_id"]] = item
        except Exception as error:
            internal_pages.append(
                {
                    "institution": institution["institution"],
                    "slug": slug,
                    "country": country,
                    "continent": continent,
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
    for item in discovered_items.values():
        video_links.append(
            {
                "institution": institution["institution"],
                "slug": slug,
                "country": country,
                "continent": continent,
                "repository_code": EUSCREEN_REPOSITORY_CODE,
                "archive_type": EUSCREEN_ARCHIVE_TYPE,
                "euscreen_detail_url": EUSCREEN_COLLECTIONS_URL,
                "content_available_in_source": True,
                "website_available": True,
                "partner_site": item.get("provider") or external_url,
                "platform": "EUscreen",
                "video_link": item["item_url"],
                "video_title": item.get("title", ""),
                "video_subject": item.get("provider", ""),
                "video_description": item.get("description", ""),
                "video_published_at": "",
            }
        )

    summary = [
        {
            "institution": institution["institution"],
            "slug": slug,
            "country": country,
            "continent": continent,
            "repository_code": EUSCREEN_REPOSITORY_CODE,
            "archive_type": EUSCREEN_ARCHIVE_TYPE,
            "euscreen_detail_url": EUSCREEN_COLLECTIONS_URL,
            "content_available_in_source": True,
            "website_available": True,
            "partner_site": external_url,
            "partner_domain": normalize_domain(external_url),
            "status": "ok",
            "http_code": 200,
            "integrity_status": "integro",
            "final_url": EUSCREEN_COLLECTIONS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_signals,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "media" if video_links else "baixa",
            "warning": "",
            "error": "",
        }
    ]

    return institutions, summary, video_links, internal_pages


__all__ = [
    "collect_euscreen_dataset",
    "collect_euscreen_institutions",
]
