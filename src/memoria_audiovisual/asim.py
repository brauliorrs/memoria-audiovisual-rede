from __future__ import annotations

import json
import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    ASIM_EFG_FILM_COLLECTION_URL,
    ASIM_EFG_PAGE_URL,
    ASIM_EFG_SEARCH_URL,
    ASIM_HOME_URL,
    ASIM_VIDEO_FUNDS_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ASIM_REPOSITORY_CODE = "ES-ASIM"
ASIM_ARCHIVE_TYPE = "Institutional film and audiovisual archive"
ASIM_COUNTRY = normalize_country("Spain")
ASIM_INSTITUTION_NAME = "Arxiu del So i de la Imatge de Mallorca"
ASIM_PLATFORM_LABEL = "European Film Gateway"
ASIM_MAX_SEARCH_PAGES = 20
ASIM_REQUEST_PAUSE = 0.05

ASIM_DETAIL_LABELS = {
    "Collection:",
    "Colour:",
    "Date:",
    "Description:",
    "Director:",
    "Document type:",
    "Genre:",
    "Keywords:",
    "Language:",
    "Other title(s):",
    "Production company:",
    "Provider:",
    "Rights:",
    "Runtime:",
    "Sound:",
    "Year:",
}

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "ca-ES,es;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(0.5 * (attempt + 1))
    raise last_error


def _search_page_url(page_index):
    if page_index <= 0:
        return ASIM_EFG_SEARCH_URL
    return f"{ASIM_EFG_SEARCH_URL}?page={page_index}%2C0%2C0"


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": ASIM_REPOSITORY_CODE,
        "archive_type": ASIM_ARCHIVE_TYPE,
        "asim_detail_url": ASIM_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ASIM_EFG_SEARCH_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def collect_asim_institutions():
    return [
        {
            "institution": ASIM_INSTITUTION_NAME,
            "slug": slugify(ASIM_INSTITUTION_NAME),
            "country": ASIM_COUNTRY,
            "continent": country_to_continent(ASIM_COUNTRY),
            "repository_code": ASIM_REPOSITORY_CODE,
            "archive_type": ASIM_ARCHIVE_TYPE,
            "asim_detail_url": ASIM_HOME_URL,
            "external_url": ASIM_EFG_SEARCH_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_asim_search_page(html, page_url=ASIM_EFG_SEARCH_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    detail_urls = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").split(";jsessionid=", 1)[0]
        absolute_url = urljoin(page_url, href)
        if "/detail/" in absolute_url and "asim::" in absolute_url:
            detail_urls.append(absolute_url)
    return list(dict.fromkeys(detail_urls))


def _extract_record_id(url):
    if "asim::" in str(url):
        return str(url).rsplit("asim::", 1)[-1].split("?", 1)[0]
    return quote(str(url).rstrip("/").rsplit("/", 1)[-1])


def _extract_metadata(lines):
    metadata = {}
    for index, line in enumerate(lines):
        if line not in ASIM_DETAIL_LABELS:
            continue
        values = []
        next_index = index + 1
        while next_index < len(lines):
            next_line = lines[next_index]
            if next_line in ASIM_DETAIL_LABELS or next_line in {"Related Names", "View as PDF", "Secondary links english"}:
                break
            if next_line.startswith("View at "):
                break
            values.append(next_line)
            next_index += 1
        metadata[line.rstrip(":")] = _clean_text(" ".join(values))
    return metadata


def _extract_player_source(soup):
    video = soup.find("video")
    if not video or not video.get("data-setup"):
        return ""
    try:
        setup = json.loads(video["data-setup"])
    except Exception:
        return ""
    sources = setup.get("sources") or []
    if not sources:
        return ""
    return _clean_text(sources[0].get("src", ""))


def _extract_external_view_url(soup, page_url):
    for anchor in soup.select("a[href]"):
        label = _clean_text(anchor.get_text(" ", strip=True))
        if label.startswith("View at "):
            return urljoin(page_url, anchor["href"])
    return ""


def parse_asim_detail_page(html, page_url):
    soup = BeautifulSoup(html or "", "html.parser")
    lines = [_clean_text(line) for line in soup.get_text("\n", strip=True).split("\n")]
    lines = [line for line in lines if line]
    metadata = _extract_metadata(lines)
    title = _clean_text((soup.find("h1") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    media_source_url = _extract_player_source(soup)
    external_view_url = _extract_external_view_url(soup, page_url)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública do ASIM no European Film Gateway, com acesso mediado por EFG/Mémoire Filmique e player quando detectado.",
                f"título alternativo: {metadata.get('Other title(s)', '')}" if metadata.get("Other title(s)") else "",
                f"gênero: {metadata.get('Genre', '')}" if metadata.get("Genre") else "",
                f"duração: {metadata.get('Runtime', '')}" if metadata.get("Runtime") else "",
                f"coleção: {metadata.get('Collection', '')}" if metadata.get("Collection") else "",
                f"direção: {metadata.get('Director', '')}" if metadata.get("Director") else "",
                f"produtora: {metadata.get('Production company', '')}" if metadata.get("Production company") else "",
                f"cor: {metadata.get('Colour', '')}" if metadata.get("Colour") else "",
                f"som: {metadata.get('Sound', '')}" if metadata.get("Sound") else "",
                f"direitos: {metadata.get('Rights', '')}" if metadata.get("Rights") else "",
                f"fonte de mídia: {media_source_url}" if media_source_url else "",
                f"ver também: {external_view_url}" if external_view_url else "",
                metadata.get("Description", ""),
            ]
            if value
        ),
        limit=1200,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "title": title,
        "detail_url": page_url,
        "media_source_url": media_source_url,
        "external_view_url": external_view_url,
        "genre": metadata.get("Genre", ""),
        "keywords": metadata.get("Keywords", ""),
        "year": metadata.get("Year", ""),
        "runtime": metadata.get("Runtime", ""),
        "provider": metadata.get("Provider", ""),
        "rights": metadata.get("Rights", ""),
        "description": description,
        "has_public_player": bool(media_source_url),
    }


def _record_to_video_row(institution, record):
    subject = _clean_text(" | ".join(value for value in [record.get("genre"), record.get("keywords")] if value))
    return {
        **_base_row(institution),
        "partner_site": ASIM_EFG_SEARCH_URL,
        "platform": ASIM_PLATFORM_LABEL,
        "video_link": record.get("detail_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": subject,
        "video_description": record.get("description", ""),
        "video_published_at": record.get("year", ""),
    }


def collect_asim_dataset():
    institutions = collect_asim_institutions()
    institution = institutions[0]
    internal_pages = []
    discovered_detail_urls = []
    records = []
    page_errors = []
    detail_errors = []

    for url, warning in [
        (ASIM_HOME_URL, "Página oficial do Arxiu del So i de la Imatge de Mallorca."),
        (ASIM_VIDEO_FUNDS_URL, "Página oficial de fundos videográficos do ASIM."),
        (ASIM_EFG_PAGE_URL, "Página do ASIM como arquivo contribuinte no European Film Gateway."),
        (ASIM_EFG_FILM_COLLECTION_URL, "Página de coleção fílmica do ASIM no European Film Gateway."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            page_errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page_index in range(ASIM_MAX_SEARCH_PAGES):
        search_url = _search_page_url(page_index)
        try:
            response = _fetch(search_url)
            detail_urls = parse_asim_search_page(response.text, response.url)
            if not detail_urls and page_index > 0:
                break
            discovered_detail_urls.extend(detail_urls)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(detail_urls),
                    len(detail_urls),
                    f"Página {page_index + 1} da coleção ASIM visível no European Film Gateway.",
                )
            )
        except Exception as error:
            page_errors.append(f"{search_url}: {error}")
            internal_pages.append(_internal_page_row(institution, search_url, "erro", error=str(error)))

    discovered_detail_urls = list(dict.fromkeys(discovered_detail_urls))
    for detail_url in discovered_detail_urls:
        try:
            response = _fetch(detail_url)
            record = parse_asim_detail_page(response.text, response.url)
            records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    int(record.get("has_public_player", False)),
                    "Ficha pública de vídeo do ASIM no EFG, com metadados e player/link externo quando disponível.",
                )
            )
        except Exception as error:
            detail_errors.append(f"{detail_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_url,
                    "erro",
                    warning="Falha ao abrir ficha pública do ASIM no EFG; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        time.sleep(ASIM_REQUEST_PAUSE)

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_collection = bool(discovered_detail_urls) and len(records) == len(discovered_detail_urls) and not detail_errors
    embedded_total = sum(1 for record in records if record.get("has_public_player"))
    summary_warning = (
        "Corpus institucional incorporado pela coleção pública do ASIM no European Film Gateway, "
        f"com {len(records)} de {len(discovered_detail_urls)} fichas materializadas nesta rodada. "
        "A unidade metodológica é o arquivo ASIM; a superfície de acesso é mediada por EFG/Mémoire/Vimeo. "
        "Nenhum arquivo de mídia é baixado."
    )
    if not complete_collection:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha de paginação ou ficha."

    summary = [
        {
            **_base_row(institution),
            "partner_site": ASIM_EFG_SEARCH_URL,
            "partner_domain": normalize_domain(ASIM_EFG_SEARCH_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_collection else "acessivel" if video_links else "instavel",
            "final_url": ASIM_EFG_SEARCH_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_collection else "media",
            "warning": summary_warning,
            "error": "; ".join([*page_errors, *detail_errors]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "ASIM_MAX_SEARCH_PAGES",
    "collect_asim_dataset",
    "collect_asim_institutions",
    "parse_asim_detail_page",
    "parse_asim_search_page",
]
