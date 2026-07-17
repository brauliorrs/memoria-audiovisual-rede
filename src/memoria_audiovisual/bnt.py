import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    BNT_ARCHIVE_AZ_URL,
    BNT_FILE_ARCHIVE_URL,
    BNT_FILM_ARCHIVE_URL,
    BNT_HOME_URL,
    BNT_LARGEST_AV_ARCHIVE_URL,
    BNT_SHOWS_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


BNT_REPOSITORY_CODE = "BG-BNT"
BNT_ARCHIVE_TYPE = "Public television audiovisual archive"
BNT_COUNTRY = normalize_country("Bulgaria")
BNT_INSTITUTION_NAME = "Bulgarian National Television"
BNT_PLATFORM_LABEL = "BNT.bg"
BNT_REQUEST_PAUSE_SECONDS = 0.35

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "bg,en;q=0.8,pt-BR;q=0.6"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, *, retries=4):
    last_error = None
    for attempt in range(retries):
        try:
            if attempt:
                time.sleep((attempt + 1) * BNT_REQUEST_PAUSE_SECONDS)
            return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        except Exception as error:
            last_error = error
    raise last_error


def _archive_page_url(page_number):
    return BNT_ARCHIVE_AZ_URL if page_number == 1 else f"{BNT_ARCHIVE_AZ_URL}?page={page_number}"


def _max_page_from_html(html_text):
    page_numbers = [int(value) for value in re.findall(r"page=(\d+)", html_text or "")]
    return max(page_numbers) if page_numbers else 1


def _extract_archive_entries(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    entries = []
    for box in soup.select(".accent-news"):
        link = box.find("a", href=True)
        if not link:
            continue
        href = link.get("href", "")
        if "/bg/a/" not in href and "/news/" not in href:
            continue
        text = _clean_text(box.get_text(" ", strip=True))
        entries.append(
            {
                "title": _clean_text(link.get("title") or link.get_text(" ", strip=True) or text),
                "listing_text": text,
                "url": urljoin(BNT_ARCHIVE_AZ_URL, href),
            }
        )
    return entries


def _extract_video_sources(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    sources = []
    for video in soup.find_all("video"):
        data_setup = video.get("data-setup") or ""
        if data_setup:
            try:
                payload = json.loads(data_setup)
                for source in payload.get("sources") or []:
                    source_url = source.get("src")
                    if source_url:
                        sources.append(source_url)
            except Exception:
                pass
        for source in video.find_all("source", src=True):
            sources.append(source["src"])
    for match in re.finditer(r"https?://[^\"'\s<>]+?\.(?:mp4|m3u8)(?:\?[^\"'\s<>]+)?", html_text or ""):
        sources.append(match.group(0))
    return sorted(dict.fromkeys(_clean_text(source) for source in sources if _clean_text(source)))


def _extract_date(text):
    match = re.search(r"(\d{1,2}):(\d{2}),\s*(\d{2})\.(\d{2})\.(\d{4})", text or "")
    if not match:
        return ""
    _hour, _minute, day, month, year = match.groups()
    return f"{year}-{month}-{day}"


def collect_bnt_institutions():
    return [
        {
            "institution": BNT_INSTITUTION_NAME,
            "slug": slugify(BNT_INSTITUTION_NAME),
            "country": BNT_COUNTRY,
            "continent": country_to_continent(BNT_COUNTRY),
            "repository_code": BNT_REPOSITORY_CODE,
            "archive_type": BNT_ARCHIVE_TYPE,
            "bnt_detail_url": BNT_HOME_URL,
            "external_url": BNT_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_bnt_detail_html(page_url, html_text, *, listing_title="", listing_text="", page_number=1):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title_node = soup.find("h1") or soup.find("title")
    title = _clean_text(title_node.get_text(" ", strip=True) if title_node else listing_title)
    description_node = (
        soup.select_one(".news-descr .small-txt-wrap")
        or soup.select_one(".tab-holder-2 .small-txt-wrap")
        or soup.select_one(".small-txt-wrap")
    )
    description = _clean_text(description_node.get_text(" ", strip=True) if description_node else "", limit=1000)
    body_text = _clean_text(soup.get_text(" ", strip=True))
    video_sources = _extract_video_sources(html_text)
    video_source_note = "; ".join(video_sources[:3])
    note = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do recorte Архив (А-Я) da BNT.",
                f"página da listagem: {page_number}",
                f"título na listagem: {listing_title}" if listing_title and listing_title != title else "",
                f"fonte de mídia: {video_source_note}" if video_source_note else "",
                description,
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": page_url.rstrip("/").rsplit("/", 1)[-1],
        "source_kind": "bnt_archive_az_detail",
        "video_link": page_url,
        "page_url": page_url,
        "platform": BNT_PLATFORM_LABEL,
        "title": title,
        "subject": "Архив (А-Я)",
        "description": note,
        "date": _extract_date(body_text) or _extract_date(listing_text),
        "page_number": page_number,
        "embedded": bool(video_sources),
        "video_sources": video_sources,
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": BNT_REPOSITORY_CODE,
        "archive_type": BNT_ARCHIVE_TYPE,
        "bnt_detail_url": BNT_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": BNT_ARCHIVE_AZ_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": BNT_ARCHIVE_AZ_URL,
        "platform": record.get("platform", BNT_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_bnt_dataset():
    institutions = collect_bnt_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_url = {}
    errors = []
    max_page = 1
    listed_entries_total = 0

    contextual_pages = [
        (BNT_HOME_URL, "Página institucional da Bulgarian National Television."),
        (BNT_SHOWS_URL, "Lista pública de programas; contexto, não rota principal do corpus."),
        (BNT_ARCHIVE_AZ_URL, "Categoria pública Архив (А-Я), rota principal do corpus."),
        (BNT_FILM_ARCHIVE_URL, "Página institucional do arquivo fílmico; descreve acervo interno de filmes."),
        (BNT_FILE_ARCHIVE_URL, "Página institucional do arquivo digital/de arquivos em ficheiro; descreve acervo interno."),
        (BNT_LARGEST_AV_ARCHIVE_URL, "Página pública sobre o arquivo audiovisual da BNT; contexto metodológico."),
    ]
    for url, warning in contextual_pages:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= max_page:
        url = _archive_page_url(page)
        try:
            response = _fetch(url)
            response.raise_for_status()
            if page == 1:
                max_page = _max_page_from_html(response.text)
            entries = _extract_archive_entries(response.text)
            listed_entries_total += len(entries)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    0,
                    0,
                    f"Página {page} de {max_page} da categoria pública Архив (А-Я); {len(entries)} entradas listadas.",
                )
            )
            for entry in entries:
                try:
                    time.sleep(BNT_REQUEST_PAUSE_SECONDS)
                    detail_response = _fetch(entry["url"])
                    detail_response.raise_for_status()
                    record = parse_bnt_detail_html(
                        detail_response.url,
                        detail_response.text,
                        listing_title=entry["title"],
                        listing_text=entry["listing_text"],
                        page_number=page,
                    )
                    records_by_url.setdefault(record["video_link"], record)
                    internal_pages.append(
                        _internal_page_row(
                            institution,
                            detail_response.url,
                            "ok",
                            detail_response.status_code,
                            1 if record["embedded"] else 0,
                            1 if record["embedded"] else 0,
                            "Página de detalhe da categoria Архив (А-Я); incorporada ao catálogo apenas quando há player público.",
                        )
                    )
                except Exception as error:
                    errors.append(f"{entry['url']}: {error}")
                    internal_pages.append(
                        _internal_page_row(
                            institution,
                            entry["url"],
                            "erro",
                            warning="Falha ao abrir detalhe listado em Архив (А-Я).",
                            error=str(error),
                        )
                    )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    "erro",
                    warning="Falha em página paginada da categoria Архив (А-Я); completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        page += 1

    video_records = [record for record in records_by_url.values() if record.get("embedded")]
    video_links = [_record_to_video_row(institution, record) for record in video_records]
    complete_route = bool(listed_entries_total) and not errors
    summary_warning = (
        "Corpus institucional incorporado pela categoria pública Архив (А-Я) do site BNT.bg. "
        f"A rodada percorreu {max_page} páginas de listagem, abriu {listed_entries_total} páginas de detalhe "
        f"e materializou {len(video_links)} registros com player público/MP4. O recorte não equivale ao acervo "
        "audiovisual interno total da BNT, ao arquivo fílmico declarado, ao arquivo digital, ao YouTube ou a "
        "serviços internos de preservação/licenciamento."
    )
    if errors:
        summary_warning = f"{summary_warning} A rodada registrou {len(errors)} erros técnicos pontuais."

    summary = [
        {
            **_base_row(institution),
            "partner_site": BNT_ARCHIVE_AZ_URL,
            "partner_domain": normalize_domain(BNT_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_route else "acessivel" if video_links else "instavel",
            "final_url": BNT_ARCHIVE_AZ_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_route else "media",
            "warning": summary_warning,
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "BNT_PLATFORM_LABEL",
    "collect_bnt_dataset",
    "collect_bnt_institutions",
    "parse_bnt_detail_html",
]
