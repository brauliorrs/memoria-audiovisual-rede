from __future__ import annotations

import html
import re
import time
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    EYE_COLLECTION_RESEARCH_URL,
    EYE_FILM_DATABASE_URL,
    EYE_FILM_FRAGMENT_LIST_URL,
    EYE_FILM_PLAYER_URL,
    EYE_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


EYE_REPOSITORY_CODE = "NL-EYE"
EYE_ARCHIVE_TYPE = "National film museum with public film-fragment catalogue"
EYE_COUNTRY = normalize_country("Netherlands")
EYE_INSTITUTION_NAME = "Eye Filmmuseum"
EYE_PLATFORM_LABEL = "Eye Filmdatabase"
EYE_SOURCE_LABEL = "Eye Filmdatabase: films with film fragment"
EYE_EXPECTED_FRAGMENT_TOTAL = 630
EYE_PAGE_DELAY_SECONDS = 0.15


@dataclass(frozen=True)
class EyeListPage:
    url: str
    status_code: int | str
    html_text: str = ""
    error: str = ""


SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept-Language": "en,nl;q=0.9,pt-BR;q=0.7",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _list_url(page_index):
    if int(page_index) <= 0:
        return EYE_FILM_FRAGMENT_LIST_URL
    separator = "&" if "?" in EYE_FILM_FRAGMENT_LIST_URL else "?"
    return f"{EYE_FILM_FRAGMENT_LIST_URL}{separator}page={int(page_index)}"


def _fetch(url):
    try:
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        return EyeListPage(response.url, response.status_code, response.text)
    except requests.RequestException as error:
        return EyeListPage(url, "erro", "", str(error))


def collect_eye_institutions():
    return [
        {
            "institution": EYE_INSTITUTION_NAME,
            "slug": slugify(EYE_INSTITUTION_NAME),
            "country": EYE_COUNTRY,
            "continent": country_to_continent(EYE_COUNTRY),
            "repository_code": EYE_REPOSITORY_CODE,
            "archive_type": EYE_ARCHIVE_TYPE,
            "eye_detail_url": EYE_COLLECTION_RESEARCH_URL,
            "external_url": EYE_FILM_FRAGMENT_LIST_URL,
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
        "repository_code": EYE_REPOSITORY_CODE,
        "archive_type": EYE_ARCHIVE_TYPE,
        "eye_detail_url": EYE_COLLECTION_RESEARCH_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _record_id_from_url(url):
    path = urlparse(str(url or "")).path.rstrip("/")
    node_match = re.search(r"/node/(\d+)$", path)
    if node_match:
        return f"node-{node_match.group(1)}"
    return path.rsplit("/", 1)[-1] if path else ""


def _list_result_items(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    items = soup.select(".view-content li.packery-item")
    return items or soup.select(".view-content .node-collection-movie")


def extract_eye_declared_fragment_total(html_text):
    text = _clean_text(html_text)
    match = re.search(r"with film fragment\s+([\d.]+)", text, flags=re.I)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_eye_max_page(html_text):
    pages = []
    for match in re.finditer(r"[?&]page=(\d+)", html.unescape(html_text or "")):
        pages.append(int(match.group(1)))
    return max(pages) if pages else 0


def parse_eye_fragment_list_page(html_text, page_url=EYE_FILM_FRAGMENT_LIST_URL):
    records = []
    seen = set()
    for item in _list_result_items(html_text):
        anchor = item.select_one("h2 a[href]") or item.find("a", href=True)
        if not anchor:
            continue
        detail_url = urljoin(page_url, html.unescape(anchor.get("href", "")))
        if "/collection/film-history/film/" not in detail_url and not re.search(r"/node/\d+/?$", detail_url):
            continue
        record_id = _record_id_from_url(detail_url)
        if not record_id or record_id == "all" or record_id in seen:
            continue
        seen.add(record_id)
        title = _clean_text(anchor.get_text(" ", strip=True), limit=300)
        image = item.find("img")
        thumbnail_url = urljoin(page_url, image.get("src", "")) if image and image.get("src") else ""
        description = _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública do Eye Filmdatabase filtrada por registros com fragmento de filme.",
                    "A listagem oficial declara presença de film fragment; a ficha é o local público do player.",
                    f"thumbnail: {thumbnail_url}" if thumbnail_url else "",
                ]
                if value
            ),
            limit=1200,
        )
        records.append(
            {
                "record_id": record_id,
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": EYE_PLATFORM_LABEL,
                "title": title,
                "subject": "film fragment; Dutch film history; Eye Filmdatabase",
                "description": description,
                "date": "",
                "thumbnail_url": thumbnail_url,
            }
        )
    return records


def _internal_page_row(institution, page, record_count=0, warning=""):
    ok = isinstance(page.status_code, int) and page.status_code < 400
    return {
        **_base_row(institution),
        "partner_site": EYE_FILM_FRAGMENT_LIST_URL,
        "internal_page": page.url,
        "status": "ok" if ok else "erro",
        "http_code": page.status_code,
        "video_links_found": record_count,
        "embedded_signals": record_count,
        "warning": warning,
        "error": page.error,
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": EYE_FILM_FRAGMENT_LIST_URL,
        "platform": EYE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_eye_dataset(fetcher=_fetch, sleep_seconds=EYE_PAGE_DELAY_SECONDS):
    institutions = collect_eye_institutions()
    institution = institutions[0]
    rows_internal_pages = []
    records_by_id = {}
    declared_total = 0
    max_page = 0
    errors = []

    first_page = fetcher(_list_url(0))
    if first_page.status_code == 200:
        declared_total = extract_eye_declared_fragment_total(first_page.html_text)
        max_page = extract_eye_max_page(first_page.html_text)
    else:
        errors.append(first_page.error or f"HTTP {first_page.status_code}")

    for page_index in range(0, max_page + 1):
        page = first_page if page_index == 0 else fetcher(_list_url(page_index))
        if page_index and sleep_seconds:
            time.sleep(sleep_seconds)
        records = parse_eye_fragment_list_page(page.html_text, page.url) if page.status_code == 200 else []
        for record in records:
            records_by_id[record["record_id"]] = record
        rows_internal_pages.append(
            _internal_page_row(
                institution,
                page,
                record_count=len(records),
                warning=(
                    "Listagem oficial de film fragments; detalhes e embeds externos não são rastreados em massa "
                    "nesta rodada para manter coleta leve e reprodutível."
                ),
            )
        )

    rows_video_links = [
        _record_to_video_row(institution, record)
        for record in sorted(records_by_id.values(), key=lambda item: (item.get("title", ""), item["record_id"]))
    ]
    total_records = len(rows_video_links)
    expected_total = declared_total or EYE_EXPECTED_FRAGMENT_TOTAL
    complete = total_records == expected_total
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": EYE_FILM_FRAGMENT_LIST_URL,
            "partner_domain": normalize_domain(EYE_FILM_FRAGMENT_LIST_URL),
            "status": "ok" if total_records else "sem_video_publico",
            "http_code": "200" if first_page.status_code == 200 else first_page.status_code,
            "integrity_status": "integro" if complete else "acessivel" if total_records else "instavel",
            "final_url": EYE_FILM_FRAGMENT_LIST_URL,
            "video_links_found_total": total_records,
            "embedded_video_signals_total": total_records,
            "candidate_internal_pages": len(rows_internal_pages),
            "priority_review": not complete,
            "warning": (
                f"Listagem pública completa de registros com film fragment: {total_records}/{expected_total}. "
                "A etapa atual registra as fichas oficiais como locais públicos dos vídeos; extração dos embeds "
                "YouTube/Vimeo deve ser incremental por causa do Crawl-delay e da camada de consentimento."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, rows_internal_pages


__all__ = [
    "collect_eye_dataset",
    "collect_eye_institutions",
    "extract_eye_declared_fragment_total",
    "extract_eye_max_page",
    "parse_eye_fragment_list_page",
]
