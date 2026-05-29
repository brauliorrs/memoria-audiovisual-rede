import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    ARCHIPOP_FILMS_LIST_URL_TEMPLATE,
    ARCHIPOP_FILMS_URL,
    ARCHIPOP_HOME_URL,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ARCHIPOP_REPOSITORY_CODE = "FR-ARCHIPOP"
ARCHIPOP_ARCHIVE_TYPE = "Institutional audiovisual archive"
ARCHIPOP_COUNTRY = normalize_country("France")
ARCHIPOP_INSTITUTION_NAME = "ARCHIPOP"
ARCHIPOP_PLATFORM_LABEL = "Archipop"
ARCHIPOP_MAX_LIST_PAGES = 4
ARCHIPOP_FILM_URL_PATTERN = re.compile(r"/les-films-.+-570-\d+-\d+-0\.html$")

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
        ),
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def collect_archipop_institutions():
    return [
        {
            "institution": ARCHIPOP_INSTITUTION_NAME,
            "slug": slugify(ARCHIPOP_INSTITUTION_NAME),
            "country": ARCHIPOP_COUNTRY,
            "continent": country_to_continent(ARCHIPOP_COUNTRY),
            "repository_code": ARCHIPOP_REPOSITORY_CODE,
            "archive_type": ARCHIPOP_ARCHIVE_TYPE,
            "archipop_detail_url": ARCHIPOP_HOME_URL,
            "external_url": ARCHIPOP_FILMS_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_archipop_list_page(html, base_url=ARCHIPOP_FILMS_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    links = {}
    for anchor in soup.find_all("a", href=True):
        film_url = urljoin(base_url, anchor["href"])
        if ARCHIPOP_FILM_URL_PATTERN.search(film_url):
            title = _clean_text(anchor.get_text(" ", strip=True))
            links.setdefault(film_url, title)
    return [{"film_url": url, "title": title} for url, title in links.items()]


def _parse_meta_items(soup):
    metadata = {}
    for item in soup.select("li.val"):
        text = _clean_text(item.get_text(" ", strip=True))
        if ":" in text:
            key, value = text.split(":", 1)
            metadata[_clean_text(key).lower()] = _clean_text(value)
    return metadata


def _extract_record_id(url):
    match = re.search(r"-570-(\d+)-", url)
    return match.group(1) if match else ""


def parse_archipop_film_page(html, page_url):
    soup = BeautifulSoup(html or "", "html.parser")
    titles = [_clean_text(heading.get_text(" ", strip=True)) for heading in soup.find_all("h1")]
    title = next((value for value in titles if value and value.lower() != "les films"), "")
    metadata = _parse_meta_items(soup)
    description = _clean_text(
        (soup.select_one(".Resume") or soup.select_one(".diaMain") or soup).get_text(" ", strip=True),
        limit=900,
    )
    keywords = _clean_text(
        (soup.select_one(".diaKeywords") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True),
        limit=400,
    )
    iframe = soup.find("iframe", src=True)
    embed_url = urljoin(page_url, iframe["src"]) if iframe else ""
    support = metadata.get("support(s)", "")
    return {
        "record_id": _extract_record_id(page_url) or support,
        "title": title,
        "film_url": page_url,
        "embed_url": embed_url,
        "year": metadata.get("année(s)", ""),
        "duration": metadata.get("durée", ""),
        "creator": metadata.get("cinéaste(s)", ""),
        "format": metadata.get("format", ""),
        "sound": metadata.get("son", ""),
        "genre": metadata.get("genre", ""),
        "collection": metadata.get("collection", ""),
        "support": support,
        "description": description,
        "keywords": keywords,
        "has_public_player": bool(embed_url),
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": ARCHIPOP_REPOSITORY_CODE,
        "archive_type": ARCHIPOP_ARCHIVE_TYPE,
        "archipop_detail_url": ARCHIPOP_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _record_to_video_row(institution, record):
    notes = [
        f"registro ARCHIPOP {record.get('record_id', '')}",
        f"player incorporado: {record.get('embed_url', '')}" if record.get("embed_url") else "sem player incorporado detectado",
        f"duração: {record.get('duration', '')}" if record.get("duration") else "",
        f"formato: {record.get('format', '')}" if record.get("format") else "",
        f"som: {record.get('sound', '')}" if record.get("sound") else "",
        f"coleção: {record.get('collection', '')}" if record.get("collection") else "",
        record.get("description", ""),
    ]
    return {
        **_base_row(institution),
        "partner_site": ARCHIPOP_FILMS_URL,
        "platform": ARCHIPOP_PLATFORM_LABEL,
        "video_link": record.get("film_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("keywords") or record.get("genre", ""),
        "video_description": _clean_text(" | ".join(note for note in notes if note), limit=900),
        "video_published_at": record.get("year", ""),
    }


def collect_archipop_dataset():
    institutions = collect_archipop_institutions()
    institution = institutions[0]
    discovered_links = {}
    internal_pages = []
    records = []
    embedded_signals = 0

    for page in range(ARCHIPOP_MAX_LIST_PAGES):
        list_url = ARCHIPOP_FILMS_LIST_URL_TEMPLATE.format(page=page)
        try:
            response = SESSION.get(list_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            page_links = parse_archipop_list_page(response.text, response.url)
            for item in page_links:
                discovered_links.setdefault(item["film_url"], item)
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": ARCHIPOP_FILMS_URL,
                    "internal_page": response.url,
                    "status": "ok",
                    "http_code": response.status_code,
                    "video_links_found": len(page_links),
                    "embedded_signals": len(page_links),
                    "warning": "Página de listagem pública do catálogo Les Films.",
                    "error": "",
                }
            )
        except Exception as error:
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": ARCHIPOP_FILMS_URL,
                    "internal_page": list_url,
                    "status": "erro",
                    "http_code": "",
                    "video_links_found": 0,
                    "embedded_signals": 0,
                    "warning": "",
                    "error": str(error),
                }
            )

    for index, film_url in enumerate(discovered_links):
        if index:
            time.sleep(SLEEP_BETWEEN_REQUESTS)
        try:
            response = SESSION.get(film_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            record = parse_archipop_film_page(response.text, response.url)
            records.append(record)
            embedded_signals += int(record["has_public_player"])
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": ARCHIPOP_FILMS_URL,
                    "internal_page": response.url,
                    "status": "ok",
                    "http_code": response.status_code,
                    "video_links_found": int(record["has_public_player"]),
                    "embedded_signals": int(record["has_public_player"]),
                    "warning": "Ficha pública de filme com metadados e, quando disponível, player incorporado.",
                    "error": "",
                }
            )
        except Exception as error:
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": ARCHIPOP_FILMS_URL,
                    "internal_page": film_url,
                    "status": "erro",
                    "http_code": "",
                    "video_links_found": 0,
                    "embedded_signals": 0,
                    "warning": "",
                    "error": str(error),
                }
            )

    video_links = [_record_to_video_row(institution, record) for record in records if record.get("has_public_player")]
    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus institucional incorporado por rota HTML pública. A coleta usa amostra leve do catálogo "
        "Les Films e registra fichas com player incorporado, sem baixar arquivos de mídia."
    )

    summary = [
        {
            **_base_row(institution),
            "partner_site": ARCHIPOP_FILMS_URL,
            "partner_domain": normalize_domain(ARCHIPOP_FILMS_URL),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "instavel",
            "final_url": ARCHIPOP_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_signals,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "media" if video_links else "alta",
            "warning": summary_warning,
            "error": summary_error,
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "ARCHIPOP_MAX_LIST_PAGES",
    "collect_archipop_dataset",
    "collect_archipop_institutions",
    "parse_archipop_film_page",
    "parse_archipop_list_page",
]
