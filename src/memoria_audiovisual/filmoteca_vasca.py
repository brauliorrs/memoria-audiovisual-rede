from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import urljoin, urldefrag

import requests
from bs4 import BeautifulSoup

from .config import (
    FILMOTECA_VASCA_CATALOG_URL,
    FILMOTECA_VASCA_HOME_URL,
    FILMOTECA_VASCA_MULTIMEDIA_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FILMOTECA_VASCA_REPOSITORY_CODE = "ES-PV-FILMOTECA-VASCA"
FILMOTECA_VASCA_ARCHIVE_TYPE = "Film archive with public multimedia collection"
FILMOTECA_VASCA_COUNTRY = normalize_country("Spain")
FILMOTECA_VASCA_INSTITUTION_NAME = "Filmoteca Vasca"
FILMOTECA_VASCA_PLATFORM_LABEL = "Vimeo"
FILMOTECA_VASCA_MAX_CRAWL_ROUNDS = 8
FILMOTECA_VASCA_MAX_CRAWL_PAGES = 600
FILMOTECA_VASCA_DETAIL_WORKERS = 5


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status: str
    html: str = ""
    error: str = ""


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _build_session():
    session = requests.Session()
    session.headers.update({**HEADERS, "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,pt-BR;q=0.7"})
    session.cookies.update(
        {
            "aceptar_marketing": "true",
            "aceptar_analiticas": "true",
            "aceptar_rrss": "true",
        }
    )
    return session


SESSION = _build_session()


def _normalize_url(url):
    return urldefrag(str(url or ""))[0].rstrip("/")


def _fetch(url, attempts=3):
    last_error = ""
    for attempt in range(attempts):
        try:
            response = SESSION.get(url, timeout=(6, REQUEST_TIMEOUT), allow_redirects=True)
            return FetchedPage(url=_normalize_url(response.url), status=str(response.status_code), html=response.text)
        except requests.RequestException as error:
            last_error = str(error)
            time.sleep(0.5 * (attempt + 1))
    return FetchedPage(url=_normalize_url(url), status="erro", error=last_error)


def collect_filmoteca_vasca_institutions():
    return [
        {
            "institution": FILMOTECA_VASCA_INSTITUTION_NAME,
            "slug": slugify(FILMOTECA_VASCA_INSTITUTION_NAME),
            "country": FILMOTECA_VASCA_COUNTRY,
            "continent": country_to_continent(FILMOTECA_VASCA_COUNTRY),
            "repository_code": FILMOTECA_VASCA_REPOSITORY_CODE,
            "archive_type": FILMOTECA_VASCA_ARCHIVE_TYPE,
            "filmoteca_vasca_detail_url": FILMOTECA_VASCA_HOME_URL,
            "external_url": FILMOTECA_VASCA_MULTIMEDIA_URL,
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
        "repository_code": FILMOTECA_VASCA_REPOSITORY_CODE,
        "archive_type": FILMOTECA_VASCA_ARCHIVE_TYPE,
        "filmoteca_vasca_detail_url": FILMOTECA_VASCA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, page, video_count=0, embedded_count=0, warning=""):
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_VASCA_MULTIMEDIA_URL,
        "internal_page": page.url,
        "status": "ok" if page.status == "200" else "erro",
        "http_code": page.status,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": page.error,
    }


def parse_filmoteca_vasca_links(html_text, page_url=FILMOTECA_VASCA_MULTIMEDIA_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = _normalize_url(urljoin(page_url, anchor["href"]))
        if href.startswith(FILMOTECA_VASCA_MULTIMEDIA_URL):
            links.append(href)
    return sorted(set(links))


def extract_filmoteca_vasca_vimeo_ids(html_text):
    ids = []
    for match in re.finditer(r"https?://(?:www\.)?vimeo\.com/(\d+)", html_text or "", flags=re.I):
        ids.append(match.group(1))
    return sorted(set(ids))


def _extract_title(soup):
    title = soup.find("h1") or soup.find("title")
    text = _clean_text(title.get_text(" ", strip=True) if title else "")
    return re.sub(r"\s*\|\s*Filmoteca Vasca.*$", "", text).strip()


def _extract_collection(soup):
    for node in soup.select(".h3, h3, span"):
        text = _clean_text(node.get_text(" ", strip=True))
        match = re.search(r"Colecci[oó]n\s*:\s*(.+)$", text, flags=re.I)
        if match:
            return _clean_text(match.group(1))
    return ""


def _extract_metadata(soup):
    metadata = {}
    for block in soup.select("div.mb-4"):
        label_node = block.find(["h2", "h3", "strong"])
        if not label_node:
            continue
        label = _clean_text(label_node.get_text(" ", strip=True)).rstrip(":")
        values = [
            _clean_text(item)
            for item in block.stripped_strings
            if _clean_text(item) and _clean_text(item) != label
        ]
        if label and values:
            metadata[label] = _clean_text(" ".join(values), limit=700)
    return metadata


def _extract_thumbnail(soup):
    node = soup.select_one("[data-thumbnail]")
    if node and node.get("data-thumbnail"):
        return urljoin(FILMOTECA_VASCA_HOME_URL, node["data-thumbnail"])
    match = re.search(r"background-image:\s*url\(([^)]+)\)", str(soup), flags=re.I)
    return urljoin(FILMOTECA_VASCA_HOME_URL, match.group(1).strip("'\"")) if match else ""


def _url_category(page_url):
    relative = str(page_url).split(FILMOTECA_VASCA_MULTIMEDIA_URL, 1)[-1].strip("/")
    parts = relative.split("/")
    return parts[0] if len(parts) > 1 else ""


def parse_filmoteca_vasca_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    vimeo_ids = extract_filmoteca_vasca_vimeo_ids(html_text)
    metadata = _extract_metadata(soup)
    collection = _extract_collection(soup) or _url_category(page_url).replace("-", " ").title()
    synopsis = metadata.get("Sinopsis / descripción", "")
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Vídeo público da seção Multimedia da Filmoteca Vasca.",
                f"coleção: {collection}" if collection else "",
                f"direção/fonte: {metadata.get('Director', '')}" if metadata.get("Director") else "",
                f"ano: {metadata.get('Año', '')}" if metadata.get("Año") else "",
                f"duração: {metadata.get('Duración', '')}" if metadata.get("Duración") else "",
                f"observações: {metadata.get('Observaciones', '')}" if metadata.get("Observaciones") else "",
                f"thumbnail: {_extract_thumbnail(soup)}" if _extract_thumbnail(soup) else "",
                synopsis,
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": vimeo_ids[0] if vimeo_ids else slugify(page_url),
        "vimeo_ids": vimeo_ids,
        "page_url": page_url,
        "title": _extract_title(soup),
        "collection": collection,
        "director": metadata.get("Director", ""),
        "year": metadata.get("Año", ""),
        "duration": metadata.get("Duración", ""),
        "observations": metadata.get("Observaciones", ""),
        "description": description,
        "thumbnail_url": _extract_thumbnail(soup),
        "source_category": _url_category(page_url),
    }


def discover_filmoteca_vasca_pages():
    seen = set()
    frontier = {FILMOTECA_VASCA_MULTIMEDIA_URL}
    pages = []
    for _ in range(FILMOTECA_VASCA_MAX_CRAWL_ROUNDS):
        batch = sorted(url for url in frontier if url not in seen)
        if not batch:
            break
        frontier = set()
        with ThreadPoolExecutor(max_workers=FILMOTECA_VASCA_DETAIL_WORKERS) as executor:
            futures = {executor.submit(_fetch, url): url for url in batch}
            for future in as_completed(futures):
                page = future.result()
                normalized_url = _normalize_url(futures[future])
                if normalized_url in seen:
                    continue
                seen.add(normalized_url)
                pages.append(page)
                if page.status == "200":
                    for link in parse_filmoteca_vasca_links(page.html, page.url):
                        if link not in seen and len(seen) + len(frontier) < FILMOTECA_VASCA_MAX_CRAWL_PAGES:
                            frontier.add(link)
        time.sleep(0.2)
    return pages


def _record_to_video_row(institution, record):
    urls = sorted(record.get("detail_urls", []))
    collections = sorted(record.get("collections", []))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                record.get("description", ""),
                f"URLs oficiais associadas: {'; '.join(urls[:8])}" if urls else "",
                f"categorias oficiais: {'; '.join(collections)}" if collections else "",
            ]
            if value
        ),
        limit=2200,
    )
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_VASCA_MULTIMEDIA_URL,
        "platform": FILMOTECA_VASCA_PLATFORM_LABEL,
        "video_link": f"https://vimeo.com/{record['vimeo_id']}",
        "video_title": record.get("title", ""),
        "video_subject": "; ".join(value for value in [*collections, record.get("director", "")] if value),
        "video_description": description,
        "video_published_at": record.get("year", ""),
    }


def _merge_record(records_by_id, parsed):
    for vimeo_id in parsed.get("vimeo_ids", []):
        record = records_by_id.setdefault(
            vimeo_id,
            {
                **parsed,
                "vimeo_id": vimeo_id,
                "detail_urls": set(),
                "collections": set(),
            },
        )
        record["detail_urls"].add(parsed["page_url"])
        if parsed.get("collection"):
            record["collections"].add(parsed["collection"])
        if parsed.get("source_category"):
            record["collections"].add(parsed["source_category"].replace("-", " ").title())


def collect_filmoteca_vasca_dataset():
    institutions = collect_filmoteca_vasca_institutions()
    institution = institutions[0]
    pages = discover_filmoteca_vasca_pages()
    records_by_id = {}
    rows_internal_pages = []
    for page in pages:
        vimeo_ids = extract_filmoteca_vasca_vimeo_ids(page.html) if page.status == "200" else []
        warning = "página oficial sem vídeo Vimeo detectado" if page.status == "200" and not vimeo_ids else ""
        rows_internal_pages.append(
            _internal_page_row(institution, page, video_count=len(vimeo_ids), embedded_count=len(vimeo_ids), warning=warning)
        )
        if vimeo_ids:
            _merge_record(records_by_id, parse_filmoteca_vasca_detail_page(page.html, page.url))

    rows_video_links = [
        _record_to_video_row(institution, record)
        for record in sorted(records_by_id.values(), key=lambda item: (item.get("title", ""), item["vimeo_id"]))
    ]
    errors_total = sum(1 for page in pages if page.status != "200")
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": FILMOTECA_VASCA_MULTIMEDIA_URL,
            "partner_domain": normalize_domain(FILMOTECA_VASCA_MULTIMEDIA_URL),
            "status": "ok" if rows_video_links else "sem_video_publico",
            "http_code": "200",
            "integrity_status": "ok" if rows_video_links and errors_total <= 2 else "revisar",
            "final_url": FILMOTECA_VASCA_MULTIMEDIA_URL,
            "video_links_found_total": len(rows_video_links),
            "embedded_video_signals_total": sum(len(record.get("detail_urls", [])) for record in records_by_id.values()),
            "candidate_internal_pages": len(pages),
            "priority_review": False,
            "warning": (
                "Corpus deduplicado por ID Vimeo; páginas oficiais duplicadas por década/coleção foram agregadas. "
                "O catálogo técnico completo permanece como fonte contextual."
            ),
            "error": f"{errors_total} páginas internas retornaram erro" if errors_total else "",
        }
    ]
    return institutions, rows_summary, rows_video_links, rows_internal_pages


__all__ = [
    "collect_filmoteca_vasca_dataset",
    "collect_filmoteca_vasca_institutions",
    "discover_filmoteca_vasca_pages",
    "extract_filmoteca_vasca_vimeo_ids",
    "parse_filmoteca_vasca_detail_page",
    "parse_filmoteca_vasca_links",
]
