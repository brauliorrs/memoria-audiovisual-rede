from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    FILMARCHIV_AUSTRIA_HOME_URL,
    FILMARCHIV_AUSTRIA_ON_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FILMARCHIV_AUSTRIA_INSTITUTION_NAME = "Filmarchiv Austria"
FILMARCHIV_AUSTRIA_REPOSITORY_CODE = "AT-FILMARCHIV-AUSTRIA"
FILMARCHIV_AUSTRIA_ARCHIVE_TYPE = "National film archive with public Filmarchiv ON streaming surface"
FILMARCHIV_AUSTRIA_COUNTRY = normalize_country("Austria")
FILMARCHIV_AUSTRIA_PLATFORM_LABEL = "Filmarchiv ON"
FILMARCHIV_AUSTRIA_MIN_VIDEO_TOTAL = 500

METADATA_LABELS = {
    "Online Verfügbar bis",
    "Originaltitel",
    "Land",
    "Jahr",
    "Ton",
    "Quelle",
    "Restaurierte Fassung",
    "Regie",
    "Buch",
    "Kamera",
    "Musik",
    "Mit",
    "Produktionsfirma",
    "Sprecher",
    "Farbe",
    "Format",
}

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "de,en;q=0.8,pt-BR;q=0.6",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _record_id_from_url(url):
    match = re.search(r"/video/([^/?#]+)", str(url or ""))
    return match.group(1) if match else ""


def _main_lines(html):
    soup = BeautifulSoup(html or "", "html.parser")
    main = soup.find("main") or soup
    return [
        _clean_text(line)
        for line in main.get_text("\n", strip=True).splitlines()
        if _clean_text(line)
    ]


def _is_metadata_label(line):
    return line.rstrip(":") in METADATA_LABELS or line.endswith(":")


def _parse_metadata(lines, start_index=0):
    metadata = {}
    index = start_index
    while index < len(lines):
        line = lines[index]
        if line == "Zurück":
            break
        label = line.rstrip(":")
        if _is_metadata_label(line) and index + 1 < len(lines):
            value = lines[index + 1]
            if value != "Zurück" and not _is_metadata_label(value):
                metadata[label] = value
                index += 2
                continue
        index += 1
    return metadata


def parse_filmarchiv_austria_listing(html, page_url=FILMARCHIV_AUSTRIA_ON_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    records_by_url = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if "/de/filmarchiv-on/video/" not in href:
            continue
        video_link = urljoin(page_url, href)
        card_text = _clean_text(anchor.get_text(" ", strip=True)).replace(
            "Your browser does not support the video tag.", ""
        )
        current = records_by_url.get(video_link, {})
        if len(card_text) > len(current.get("card_text", "")):
            records_by_url[video_link] = {
                "record_id": _record_id_from_url(video_link),
                "video_link": video_link,
                "card_text": _clean_text(card_text),
            }
    return list(records_by_url.values())


def parse_filmarchiv_austria_detail(html, video_link, card_record=None):
    soup = BeautifulSoup(html or "", "html.parser")
    lines = _main_lines(html)
    record_id = _record_id_from_url(video_link)
    title = _clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else ""
    card_record = card_record or {}
    category = ""

    title_index = -1
    if title and title in lines:
        title_index = lines.index(title)
    elif record_id in lines:
        title_index = min(len(lines) - 1, lines.index(record_id) + 1)
        title = lines[title_index]
    else:
        title = card_record.get("card_text", record_id)

    if title_index > 0:
        for line in lines[:title_index]:
            if line not in {"ON", "/", "➜ edit", record_id} and not line.startswith("f_"):
                category = line

    description_lines = []
    for line in lines[title_index + 1 :]:
        if line == "Zurück" or _is_metadata_label(line):
            break
        description_lines.append(line)

    metadata_start = title_index + 1 + len(description_lines)
    metadata = _parse_metadata(lines, metadata_start)
    year = metadata.get("Jahr", "")
    country = metadata.get("Land", "")
    available_until = metadata.get("Online Verfügbar bis", "")

    subject_parts = [
        category,
        f"país: {country}" if country else "",
        f"ano: {year}" if year else "",
        f"direção: {metadata.get('Regie')}" if metadata.get("Regie") else "",
        f"produção: {metadata.get('Produktionsfirma')}" if metadata.get("Produktionsfirma") else "",
    ]
    description_parts = [
        " ".join(description_lines),
        f"título original: {metadata.get('Originaltitel')}" if metadata.get("Originaltitel") else "",
        f"categoria Filmarchiv ON: {category}" if category else "",
        f"elenco/participantes: {metadata.get('Mit')}" if metadata.get("Mit") else "",
        f"fonte: {metadata.get('Quelle')}" if metadata.get("Quelle") else "",
        f"restauração: {metadata.get('Restaurierte Fassung')}" if metadata.get("Restaurierte Fassung") else "",
        f"disponibilidade temporal declarada até {available_until}" if available_until else "",
        "acesso público online detectado na superfície Filmarchiv ON; mídia não baixada.",
    ]
    return {
        "record_id": record_id,
        "video_link": video_link,
        "title": title,
        "subject": "; ".join(part for part in subject_parts if part),
        "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1800),
        "date": year,
        "category": category,
        "country": country,
        "available_until": available_until,
        "metadata": metadata,
        "card_text": card_record.get("card_text", ""),
    }


def _fetch_html(url):
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT))
    response.raise_for_status()
    return response.text, response.url, response.status_code


def collect_filmarchiv_austria_institutions():
    return [
        {
            "institution": FILMARCHIV_AUSTRIA_INSTITUTION_NAME,
            "slug": slugify(FILMARCHIV_AUSTRIA_INSTITUTION_NAME),
            "country": FILMARCHIV_AUSTRIA_COUNTRY,
            "continent": country_to_continent(FILMARCHIV_AUSTRIA_COUNTRY),
            "repository_code": FILMARCHIV_AUSTRIA_REPOSITORY_CODE,
            "archive_type": FILMARCHIV_AUSTRIA_ARCHIVE_TYPE,
            "filmarchiv_austria_detail_url": FILMARCHIV_AUSTRIA_HOME_URL,
            "external_url": FILMARCHIV_AUSTRIA_ON_URL,
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
        "repository_code": FILMARCHIV_AUSTRIA_REPOSITORY_CODE,
        "archive_type": FILMARCHIV_AUSTRIA_ARCHIVE_TYPE,
        "filmarchiv_austria_detail_url": FILMARCHIV_AUSTRIA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FILMARCHIV_AUSTRIA_ON_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": count,
        "embedded_signals": count,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": FILMARCHIV_AUSTRIA_ON_URL,
        "platform": FILMARCHIV_AUSTRIA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_filmarchiv_austria_dataset(fetch_html=_fetch_html):
    institutions = collect_filmarchiv_austria_institutions()
    institution = institutions[0]
    rows_internal_pages = []
    errors = []

    try:
        listing_html, listing_url, listing_status = fetch_html(FILMARCHIV_AUSTRIA_ON_URL)
        listing_records = parse_filmarchiv_austria_listing(listing_html, listing_url)
        rows_internal_pages.append(
            _internal_page_row(
                institution,
                listing_url,
                "ok",
                listing_status,
                count=len(listing_records),
                warning=(
                    "Rota pública Filmarchiv ON renderiza a união das subrotas audiovisuais "
                    "detectadas; a coleta não afirma exaustividade do acervo físico total."
                ),
            )
        )
    except Exception as error:
        listing_records = []
        errors.append(f"Filmarchiv ON: {error}")
        rows_internal_pages.append(_internal_page_row(institution, FILMARCHIV_AUSTRIA_ON_URL, "erro", error=str(error)))

    detailed_records = []
    for card_record in listing_records:
        video_link = card_record["video_link"]
        try:
            detail_html, final_url, detail_status = fetch_html(video_link)
            detailed_records.append(parse_filmarchiv_austria_detail(detail_html, final_url, card_record))
            rows_internal_pages.append(
                _internal_page_row(
                    institution,
                    final_url,
                    "ok",
                    detail_status,
                    count=1,
                    warning="Ficha pública de vídeo Filmarchiv ON coletada para metadados descritivos.",
                )
            )
        except Exception as error:
            errors.append(f"{video_link}: {error}")
            detailed_records.append(
                {
                    "record_id": card_record.get("record_id", ""),
                    "video_link": video_link,
                    "title": card_record.get("card_text", card_record.get("record_id", "")),
                    "subject": "Filmarchiv ON",
                    "description": "Ficha de vídeo detectada na listagem Filmarchiv ON, mas detalhe indisponível nesta rodada.",
                    "date": "",
                }
            )
            rows_internal_pages.append(_internal_page_row(institution, video_link, "erro", error=str(error)))

    rows_video_links = [
        _record_to_video_row(institution, record)
        for record in sorted(detailed_records, key=lambda item: (item.get("date", ""), item.get("title", "")))
    ]
    total_records = len(rows_video_links)
    complete = total_records >= FILMARCHIV_AUSTRIA_MIN_VIDEO_TOTAL
    categories = sorted({record.get("category", "") for record in detailed_records if record.get("category")})
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": FILMARCHIV_AUSTRIA_ON_URL,
            "partner_domain": normalize_domain(FILMARCHIV_AUSTRIA_HOME_URL),
            "status": "ok" if total_records else "sem_video_publico",
            "http_code": "200" if total_records else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": FILMARCHIV_AUSTRIA_ON_URL,
            "video_links_found_total": total_records,
            "embedded_video_signals_total": total_records,
            "candidate_internal_pages": len(rows_internal_pages),
            "priority_review": not complete,
            "warning": (
                f"Filmarchiv ON materializou {total_records} páginas públicas de vídeo nesta rodada. "
                f"Categorias internas detectadas: {', '.join(categories) if categories else 'não identificadas'}. "
                "O corpus representa a superfície online pública Filmarchiv ON, não o acervo físico total do Filmarchiv Austria."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, rows_internal_pages


__all__ = [
    "FILMARCHIV_AUSTRIA_MIN_VIDEO_TOTAL",
    "collect_filmarchiv_austria_dataset",
    "collect_filmarchiv_austria_institutions",
    "parse_filmarchiv_austria_detail",
    "parse_filmarchiv_austria_listing",
]
