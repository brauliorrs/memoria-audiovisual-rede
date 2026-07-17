from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup

from .config import (
    FILMOTECA_VALENCIANA_CATALOG_URL,
    FILMOTECA_VALENCIANA_HOME_URL,
    FILMOTECA_VALENCIANA_RESTORATIONS_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FILMOTECA_VALENCIANA_INSTITUTION_NAME = "Filmoteca Valenciana"
FILMOTECA_VALENCIANA_REPOSITORY_CODE = "ES-VC-FILMOTECA-VALENCIANA"
FILMOTECA_VALENCIANA_ARCHIVE_TYPE = (
    "Film archive with public restored-film streaming subset and larger restricted catalogue"
)
FILMOTECA_VALENCIANA_COUNTRY = normalize_country("Spain")
FILMOTECA_VALENCIANA_PLATFORM_LABEL = "Vimeo / Restauraciones Filmoteca Valenciana"
FILMOTECA_VALENCIANA_MIN_VIDEO_TOTAL = 60
FILMOTECA_VALENCIANA_DETAIL_WORKERS = 8
FILMOTECA_VALENCIANA_LISTING_URL = urljoin(FILMOTECA_VALENCIANA_RESTORATIONS_URL, "inicio/")
FILMOTECA_VALENCIANA_FILM_PATH_MARKERS = (
    "/cine-valenciano/",
    "/cine-espanol/",
    "/cine-extranjero/",
    "/familiar-2/",
)


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status: str
    html: str = ""
    error: str = ""


SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept-Language": "es-ES,es;q=0.9,ca;q=0.8,en;q=0.7,pt-BR;q=0.6",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _normalize_url(url):
    normalized = urldefrag(str(url or ""))[0].strip()
    return normalized.rstrip("/") + "/" if normalized else ""


def _fetch(url):
    last_error = ""
    for attempt in range(3):
        try:
            response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
            return FetchedPage(url=_normalize_url(response.url), status=str(response.status_code), html=response.text)
        except requests.RequestException as error:
            last_error = str(error)
            time.sleep(0.4 * (attempt + 1))
    return FetchedPage(url=_normalize_url(url), status="erro", error=last_error)


def collect_filmoteca_valenciana_institutions():
    return [
        {
            "institution": FILMOTECA_VALENCIANA_INSTITUTION_NAME,
            "slug": slugify(FILMOTECA_VALENCIANA_INSTITUTION_NAME),
            "country": FILMOTECA_VALENCIANA_COUNTRY,
            "continent": country_to_continent(FILMOTECA_VALENCIANA_COUNTRY),
            "repository_code": FILMOTECA_VALENCIANA_REPOSITORY_CODE,
            "archive_type": FILMOTECA_VALENCIANA_ARCHIVE_TYPE,
            "filmoteca_valenciana_detail_url": FILMOTECA_VALENCIANA_HOME_URL,
            "external_url": FILMOTECA_VALENCIANA_RESTORATIONS_URL,
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
        "repository_code": FILMOTECA_VALENCIANA_REPOSITORY_CODE,
        "archive_type": FILMOTECA_VALENCIANA_ARCHIVE_TYPE,
        "filmoteca_valenciana_detail_url": FILMOTECA_VALENCIANA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, page, video_count=0, embedded_count=0, warning=""):
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_VALENCIANA_RESTORATIONS_URL,
        "internal_page": page.url,
        "status": "ok" if page.status == "200" else "erro",
        "http_code": page.status,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": page.error,
    }


def parse_filmoteca_valenciana_listing_links(html_text, page_url=FILMOTECA_VALENCIANA_LISTING_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = _normalize_url(urljoin(page_url, anchor["href"]))
        if href.startswith(FILMOTECA_VALENCIANA_RESTORATIONS_URL) and any(
            marker in href for marker in FILMOTECA_VALENCIANA_FILM_PATH_MARKERS
        ):
            links.append(href)
    return sorted(set(links))


def extract_filmoteca_valenciana_vimeo_ids(html_text):
    ids = []
    for match in re.finditer(r"(?:player\.)?vimeo\.com/(?:video/)?(\d+)", html_text or "", flags=re.I):
        ids.append(match.group(1))
    return sorted(set(ids))


def _extract_iframe_url(soup, vimeo_id):
    iframe = soup.find("iframe", src=re.compile(rf"vimeo\.com/(?:video/)?{re.escape(vimeo_id)}", re.I))
    return iframe.get("src", "") if iframe else f"https://player.vimeo.com/video/{vimeo_id}"


def _extract_title(soup):
    title = soup.find("h1") or soup.find("title")
    text = _clean_text(title.get_text(" ", strip=True) if title else "")
    return re.sub(r"\s*[«|].*$", "", text).strip()


def _entry_text_blocks(soup):
    entry = soup.select_one(".entry") or soup.select_one(".post") or soup
    blocks = []
    for node in entry.find_all(["p", "li"], recursive=True):
        text = _clean_text(node.get_text(" ", strip=True))
        if text and text not in blocks:
            blocks.append(text)
    return [block for block in blocks if "Enlace a la ficha" not in block]


def _extract_catalog_url(soup, page_url):
    entry = soup.select_one(".entry") or soup.select_one(".post") or soup
    for anchor in entry.find_all("a", href=True):
        text = _clean_text(anchor.get_text(" ", strip=True)).lower()
        href = urljoin(page_url, anchor["href"])
        if "ficha" in text or "BRSCGI.exe" in href:
            return href
    return ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})(?:[-/]\d{2,4})?\b", str(value or ""))
    return match.group(0) if match else ""


def _extract_duration(value):
    match = re.search(r"\b\d+\s*(?:minutos|min\.?|m|′|'|’)\b", str(value or ""), flags=re.I)
    return _clean_text(match.group(0)) if match else ""


def _category_from_url(page_url):
    path = page_url.split(FILMOTECA_VALENCIANA_RESTORATIONS_URL, 1)[-1].strip("/")
    parts = path.split("/")
    labels = {
        "cine-valenciano": "Cine valenciano",
        "cine-espanol": "Cine espanhol",
        "cine-extranjero": "Cine estrangeiro",
        "familiar-2": "Cinema doméstico",
        "ficcion": "ficção",
        "no-ficcion": "não ficção",
    }
    return " / ".join(labels.get(part, part.replace("-", " ")) for part in parts[:2] if part)


def parse_filmoteca_valenciana_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    vimeo_ids = extract_filmoteca_valenciana_vimeo_ids(html_text)
    title = _extract_title(soup)
    blocks = _entry_text_blocks(soup)
    heading = blocks[0] if blocks else ""
    body = " ".join(blocks[1:]) if len(blocks) > 1 else ""
    catalog_url = _extract_catalog_url(soup, page_url)
    category = _category_from_url(page_url)
    year = _extract_year(" ".join(blocks))
    duration = _extract_duration(" ".join(blocks))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Vídeo público no subsite Restauraciones da Filmoteca Valenciana.",
                "Recorte metodológico: filmes restaurados com player Vimeo incorporado; não representa o catálogo integral do IVC.",
                f"categoria: {category}" if category else "",
                f"metadados da ficha: {heading}" if heading else "",
                f"duração: {duration}" if duration else "",
                f"ficha catalográfica: {catalog_url}" if catalog_url else "",
                body,
            ]
            if value
        ),
        limit=1800,
    )
    records = []
    for index, vimeo_id in enumerate(vimeo_ids, start=1):
        record_title = title if len(vimeo_ids) == 1 else f"{title} ({index})"
        records.append(
            {
                "record_id": vimeo_id,
                "page_url": _normalize_url(page_url),
                "video_link": _extract_iframe_url(soup, vimeo_id),
                "title": record_title,
                "subject": "; ".join(part for part in [category, heading] if part),
                "description": description,
                "date": year,
                "duration": duration,
                "category": category,
                "catalog_record_url": catalog_url,
            }
        )
    return records


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_VALENCIANA_RESTORATIONS_URL,
        "platform": FILMOTECA_VALENCIANA_PLATFORM_LABEL,
        "video_title": record["title"],
        "video_url": record["page_url"],
        "video_link": record["video_link"],
        "video_subject": record["subject"],
        "video_description": record["description"],
        "video_date": record["date"],
        "embedded": True,
    }


def collect_filmoteca_valenciana_dataset(fetch_page=_fetch):
    institutions = collect_filmoteca_valenciana_institutions()
    institution = institutions[0]
    internal_pages = []

    listing_page = fetch_page(FILMOTECA_VALENCIANA_LISTING_URL)
    film_links = parse_filmoteca_valenciana_listing_links(listing_page.html, listing_page.url)
    internal_pages.append(
        _internal_page_row(
            institution,
            listing_page,
            video_count=len(film_links),
            warning=(
                "Listagem pública em espanhol usada para evitar duplicação com a versão valenciana. "
                "O catálogo geral do IVC em porta 8080 é citado como ficha, mas não é a rota primária de streaming."
            ),
        )
    )

    records_by_id = {}
    with ThreadPoolExecutor(max_workers=FILMOTECA_VALENCIANA_DETAIL_WORKERS) as executor:
        futures = {executor.submit(fetch_page, url): url for url in film_links}
        for future in as_completed(futures):
            page = future.result()
            records = parse_filmoteca_valenciana_detail_page(page.html, page.url) if page.status == "200" else []
            for record in records:
                records_by_id.setdefault(record["record_id"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page,
                    video_count=len(records),
                    embedded_count=len(records),
                    warning="" if records else "Página de categoria ou ficha sem player Vimeo detectado.",
                )
            )

    records = sorted(records_by_id.values(), key=lambda item: (item.get("category", ""), item["title"], item["record_id"]))
    video_links = [_record_to_video_row(institution, record) for record in records]
    total_records = len(video_links)
    complete = total_records >= FILMOTECA_VALENCIANA_MIN_VIDEO_TOTAL
    summary = [
        {
            **_base_row(institution),
            "partner_site": FILMOTECA_VALENCIANA_RESTORATIONS_URL,
            "partner_domain": normalize_domain(FILMOTECA_VALENCIANA_RESTORATIONS_URL),
            "status": "ok" if total_records else "sem_video_publico_detectado",
            "http_code": listing_page.status,
            "final_url": listing_page.url,
            "video_links_found": total_records,
            "video_links_found_total": total_records,
            "internal_pages_checked": len(internal_pages),
            "candidate_internal_pages": len(internal_pages),
            "embedded_signals": total_records,
            "embedded_video_signals_total": total_records,
            "integrity_status": "integro" if complete else "instavel",
            "priority_review": not complete,
            "collection_complete": complete,
            "collection_completeness": (
                "recorte público de restaurações com Vimeo completo no momento da coleta"
                if complete
                else "recorte público abaixo do piso metodológico; reavaliar listagem"
            ),
            "warning": (
                "O corpus representa o subsite público de restaurações com player Vimeo, não o catálogo integral "
                "da Filmoteca Valenciana/IVC. O catálogo geral e pedidos de visionamento/cópia permanecem como "
                "acesso institucional condicionado."
            ),
            "error": listing_page.error,
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "FILMOTECA_VALENCIANA_MIN_VIDEO_TOTAL",
    "FILMOTECA_VALENCIANA_PLATFORM_LABEL",
    "collect_filmoteca_valenciana_dataset",
    "collect_filmoteca_valenciana_institutions",
    "extract_filmoteca_valenciana_vimeo_ids",
    "parse_filmoteca_valenciana_detail_page",
    "parse_filmoteca_valenciana_listing_links",
]
