from __future__ import annotations

import json
import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    BNFA_EFG_COLLECTION_URL,
    BNFA_EFG_PAGE_URL,
    BNFA_E_CATALOGUE_BG_URL,
    BNFA_E_CATALOGUE_EN_URL,
    BNFA_FILM_COLLECTION_URL,
    BNFA_FILM_LIBRARY_URL,
    BNFA_HOME_HTTP_URL,
    BNFA_HOME_HTTPS_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


BNFA_REPOSITORY_CODE = "BG-BNFA"
BNFA_ARCHIVE_TYPE = "National film archive"
BNFA_COUNTRY = normalize_country("Bulgaria")
BNFA_INSTITUTION_NAME = "Bulgarian National Film Archive"
BNFA_PLATFORM_LABEL = "European Film Gateway"
BNFA_MAX_SEARCH_PAGES = 30
BNFA_REQUEST_PAUSE = 0.05

BNFA_DETAIL_LABELS = {
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
SESSION.headers.update({**HEADERS, "Accept-Language": "bg,en;q=0.9,pt-BR;q=0.7"})


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
        return BNFA_EFG_COLLECTION_URL
    return f"{BNFA_EFG_COLLECTION_URL}?page={page_index}%2C0%2C0"


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": BNFA_REPOSITORY_CODE,
        "archive_type": BNFA_ARCHIVE_TYPE,
        "bnfa_detail_url": BNFA_HOME_HTTP_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": BNFA_EFG_COLLECTION_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def collect_bnfa_institutions():
    return [
        {
            "institution": BNFA_INSTITUTION_NAME,
            "slug": slugify(BNFA_INSTITUTION_NAME),
            "country": BNFA_COUNTRY,
            "continent": country_to_continent(BNFA_COUNTRY),
            "repository_code": BNFA_REPOSITORY_CODE,
            "archive_type": BNFA_ARCHIVE_TYPE,
            "bnfa_detail_url": BNFA_HOME_HTTP_URL,
            "external_url": BNFA_EFG_COLLECTION_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_bnfa_search_page(html, page_url=BNFA_EFG_COLLECTION_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    detail_urls = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").split(";jsessionid=", 1)[0]
        absolute_url = urljoin(page_url, href)
        if "/detail/" in absolute_url and "bnfa::" in absolute_url:
            detail_urls.append(absolute_url)
    return list(dict.fromkeys(detail_urls))


def extract_bnfa_result_total(html):
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"Videos?\s*\(([\d,\.]+)\s+Results?\)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return int(re.sub(r"\D", "", match.group(1)) or 0)


def _extract_record_id(url):
    if "bnfa::" in str(url):
        return str(url).rsplit("bnfa::", 1)[-1].split("?", 1)[0]
    return quote(str(url).rstrip("/").rsplit("/", 1)[-1])


def _extract_metadata(lines):
    metadata = {}
    for index, line in enumerate(lines):
        if line not in BNFA_DETAIL_LABELS:
            continue
        values = []
        next_index = index + 1
        while next_index < len(lines):
            next_line = lines[next_index]
            if next_line in BNFA_DETAIL_LABELS or next_line in {"Related Names", "View as PDF", "Secondary links english"}:
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


def _has_player_shell(html, text):
    normalized = str(html or "").lower()
    text_normalized = str(text or "").lower()
    return "video-js" in normalized or "supports html5 video" in text_normalized or "enable javascript" in text_normalized


def parse_bnfa_detail_page(html, page_url):
    soup = BeautifulSoup(html or "", "html.parser")
    lines = [_clean_text(line) for line in soup.get_text("\n", strip=True).split("\n")]
    lines = [line for line in lines if line]
    text = " ".join(lines)
    metadata = _extract_metadata(lines)
    title = _clean_text((soup.find("h1") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    media_source_url = _extract_player_source(soup)
    has_player_shell = _has_player_shell(html, text)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública da Bulgarian National Film Archive no European Film Gateway.",
                "player EFG sinalizado no HTML, sem fonte de mídia materializada na coleta estática" if has_player_shell and not media_source_url else "",
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
                metadata.get("Description", ""),
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "title": title,
        "detail_url": page_url,
        "media_source_url": media_source_url,
        "genre": metadata.get("Genre", ""),
        "keywords": metadata.get("Keywords", ""),
        "year": metadata.get("Year", ""),
        "runtime": metadata.get("Runtime", ""),
        "provider": metadata.get("Provider", ""),
        "rights": metadata.get("Rights", ""),
        "description": description,
        "has_public_player": bool(media_source_url),
        "has_player_shell": has_player_shell,
    }


def _record_to_video_row(institution, record):
    subject = _clean_text(" | ".join(value for value in [record.get("genre"), record.get("keywords")] if value))
    return {
        **_base_row(institution),
        "partner_site": BNFA_EFG_COLLECTION_URL,
        "platform": BNFA_PLATFORM_LABEL,
        "video_link": record.get("detail_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": subject,
        "video_description": record.get("description", ""),
        "video_published_at": record.get("year", ""),
    }


def collect_bnfa_dataset():
    institutions = collect_bnfa_institutions()
    institution = institutions[0]
    internal_pages = []
    discovered_detail_urls = []
    records = []
    context_errors = []
    page_errors = []
    detail_errors = []
    announced_total = 0

    for url, warning in [
        (BNFA_HOME_HTTPS_URL, "Rota HTTPS do site oficial; testada para registrar fragilidade TLS quando ocorrer."),
        (BNFA_HOME_HTTP_URL, "Site oficial da Bulgarian National Film Archive por HTTP."),
        (BNFA_FILM_LIBRARY_URL, "Página institucional da filmoteca; contexto de preservação e acesso."),
        (BNFA_FILM_COLLECTION_URL, "Página Film Collection; declara escala do acervo fílmico."),
        (BNFA_E_CATALOGUE_EN_URL, "e-Catalogue próprio em inglês; contexto, não rota principal do corpus."),
        (BNFA_E_CATALOGUE_BG_URL, "e-Catalogue próprio em búlgaro; informa desenvolvimento quando aplicável."),
        (BNFA_EFG_PAGE_URL, "Página da BNFA como arquivo contribuinte no European Film Gateway."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            context_errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page_index in range(BNFA_MAX_SEARCH_PAGES):
        search_url = _search_page_url(page_index)
        try:
            response = _fetch(search_url)
            if page_index == 0:
                announced_total = extract_bnfa_result_total(response.text)
            detail_urls = parse_bnfa_search_page(response.text, response.url)
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
                    f"Página {page_index + 1} da coleção BNFA no European Film Gateway; {announced_total or 'total não detectado'} resultados de vídeo anunciados.",
                )
            )
        except Exception as error:
            page_errors.append(f"{search_url}: {error}")
            internal_pages.append(_internal_page_row(institution, search_url, "erro", error=str(error)))

    discovered_detail_urls = list(dict.fromkeys(discovered_detail_urls))
    for detail_url in discovered_detail_urls:
        try:
            response = _fetch(detail_url)
            record = parse_bnfa_detail_page(response.text, response.url)
            records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    int(record.get("has_player_shell", False)),
                    "Ficha pública de vídeo da BNFA no EFG, com metadados audiovisuais e shell de player quando sinalizado.",
                )
            )
        except Exception as error:
            detail_errors.append(f"{detail_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_url,
                    "erro",
                    warning="Falha ao abrir ficha pública da BNFA no EFG; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        time.sleep(BNFA_REQUEST_PAUSE)

    video_links = [_record_to_video_row(institution, record) for record in records]
    reached_announced_total = not announced_total or len(records) >= announced_total
    complete_collection = bool(records) and reached_announced_total and not page_errors and not detail_errors
    player_shell_total = sum(1 for record in records if record.get("has_player_shell"))
    summary_warning = (
        "Corpus institucional incorporado pela coleção pública da Bulgarian National Film Archive no European Film Gateway. "
        f"O EFG anunciou {announced_total or 'total não detectado'} resultados de vídeo e a rodada materializou "
        f"{len(records)} fichas de {len(discovered_detail_urls)} URLs de detalhe encontradas. "
        "A rota própria e-Catalogue do site bnf.bg foi registrada como contexto e não como rota principal; "
        "nenhum arquivo de mídia é baixado."
    )
    if context_errors:
        summary_warning = f"{summary_warning} Foram registrados {len(context_errors)} problemas em páginas contextuais, sem invalidar a rota EFG."
    if not complete_collection:
        summary_warning = f"{summary_warning} A completude deve ser lida como parcial por falha de paginação, ficha ou divergência com o total anunciado."

    summary = [
        {
            **_base_row(institution),
            "partner_site": BNFA_EFG_COLLECTION_URL,
            "partner_domain": normalize_domain(BNFA_EFG_COLLECTION_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_collection else "acessivel" if video_links else "instavel",
            "final_url": BNFA_EFG_COLLECTION_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": player_shell_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_collection else "media",
            "warning": summary_warning,
            "error": "; ".join([*context_errors, *page_errors, *detail_errors]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "BNFA_MAX_SEARCH_PAGES",
    "collect_bnfa_dataset",
    "collect_bnfa_institutions",
    "extract_bnfa_result_total",
    "parse_bnfa_detail_page",
    "parse_bnfa_search_page",
]
