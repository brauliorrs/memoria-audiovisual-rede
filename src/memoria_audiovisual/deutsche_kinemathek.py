from __future__ import annotations

import re
import time
from html import unescape
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    DEUTSCHE_KINEMATHEK_DIGITAL_COLLECTION_URL,
    DEUTSCHE_KINEMATHEK_FILM_ARCHIVE_URL,
    DEUTSCHE_KINEMATHEK_HOME_URL,
    DEUTSCHE_KINEMATHEK_SEARCH_PORTAL_URL,
    DEUTSCHE_KINEMATHEK_STREAMING_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


DEUTSCHE_KINEMATHEK_REPOSITORY_CODE = "DE-DEUTSCHE-KINEMATHEK"
DEUTSCHE_KINEMATHEK_ARCHIVE_TYPE = "Film archive and museum with public curatorial streaming program"
DEUTSCHE_KINEMATHEK_COUNTRY = normalize_country("Germany")
DEUTSCHE_KINEMATHEK_INSTITUTION_NAME = "Deutsche Kinemathek / Museum für Film und Fernsehen"
DEUTSCHE_KINEMATHEK_PLATFORM_LABEL = "Deutsche Kinemathek Selects"
DEUTSCHE_KINEMATHEK_REQUEST_PAUSE = 0.1

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en,de;q=0.8,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    return response


def _first_media_source(node):
    for source in node.select("source"):
        value = _clean_text(source.get("src") or source.get("data-src"))
        if value:
            return unescape(value)
    return ""


def _extract_program_label(soup):
    text = soup.get_text(" ", strip=True)
    match = re.search(r"(Selects\s*#\s*\d+\s*\|\s*\d{1,2}\s+[A-Za-z]+[–-]\d{1,2}\s+[A-Za-z]+\s+\d{2,4})", text)
    if not match:
        match = re.search(r"(Selects\s*#\s*\d+\s*\|\s*.*?)(?:All films|$)", text)
    return _clean_text(match.group(1), limit=160) if match else "Selects"


def _extract_year(text):
    match = re.search(r"\b((?:19|20)\d{2})\b", text)
    return match.group(1) if match else ""


def _extract_duration(text):
    match = re.search(r"\b(\d{1,3})\s*min\b", text, flags=re.IGNORECASE)
    return f"{match.group(1)} min" if match else ""


def _extract_country_code(text):
    match = re.search(r"\b([A-Z]{2,4})\s+(?:19|20)\d{2}\b", text)
    return match.group(1) if match else ""


def _extract_director(text):
    match = re.search(r"\bdirected by:\s*([^,]+(?:,\s*[^,]+)*?)(?:,\s*\d{1,3}\s*min|,\s*with|,\s*rating|,\s*rated|$)", text, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"\bdirector:\s*([^,]+(?:,\s*[^,]+)*?)(?:,\s*\d{1,3}\s*min|,\s*with|,\s*rating|,\s*rated|$)", text, flags=re.IGNORECASE)
    return _clean_text(match.group(1)) if match else ""


def _normalize_card_text(card):
    text = _clean_text(card.get_text(" ", strip=True))
    return text.replace("Your browser does not support the video tag. ", "")


def parse_deutsche_kinemathek_streaming_page(html, page_url=DEUTSCHE_KINEMATHEK_STREAMING_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    program_label = _extract_program_label(soup)
    records_by_url = {}

    for card in soup.select(".view__item.basic-grid__item"):
        anchor = card.select_one('a[href*="/online/streaming/"]')
        if not anchor:
            continue
        title = _clean_text(anchor.get_text(" ", strip=True))
        detail_url = urljoin(page_url, anchor.get("href", ""))
        media_url = _first_media_source(card)
        card_text = _normalize_card_text(card)
        if not title or not detail_url or detail_url in records_by_url:
            continue
        records_by_url[detail_url] = {
            "record_id": detail_url.rstrip("/").rsplit("/", 1)[-1],
            "title": title,
            "subject": "; ".join(
                part
                for part in [
                    program_label,
                    _extract_country_code(card_text),
                    _extract_director(card_text),
                ]
                if part
            ),
            "description": _clean_text(
                " | ".join(
                    part
                    for part in [
                        "Ficha pública do programa Selects da Deutsche Kinemathek; mídia não baixada.",
                        card_text,
                        "fonte de player detectada na página pública" if media_url else "",
                    ]
                    if part
                ),
                limit=1200,
            ),
            "date": _extract_year(card_text),
            "duration": _extract_duration(card_text),
            "page_url": detail_url,
            "media_url": media_url,
            "program_label": program_label,
            "embedded": bool(media_url),
        }

    return list(records_by_url.values())


def parse_deutsche_kinemathek_detail_page(html, page_url, fallback=None):
    fallback = fallback or {}
    soup = BeautifulSoup(html or "", "html.parser")
    title_node = soup.find("h1")
    title = _clean_text(title_node.get_text(" ", strip=True) if title_node else fallback.get("title", ""))
    main = soup.select_one("main") or soup
    detail_text = _clean_text(main.get_text(" ", strip=True))
    for marker in ("Weiterschauen", "Continue watching", "load more"):
        detail_text = detail_text.split(marker, 1)[0]
    detail_text = _clean_text(detail_text.replace("Back to the streaming start page", ""), limit=1400)
    card_text = _clean_text(fallback.get("description", ""))
    media_url = fallback.get("media_url", "") or _first_media_source(main)
    subject = "; ".join(
        part
        for part in [
            fallback.get("program_label", "Selects"),
            _extract_country_code(detail_text),
            _extract_director(detail_text),
        ]
        if part
    )
    description = _clean_text(
        " | ".join(
            part
            for part in [
                "Ficha pública do programa Selects da Deutsche Kinemathek; mídia não baixada.",
                detail_text or card_text,
                "fonte de player detectada na página pública; URL assinada renovada pela própria página na rodada" if media_url else "",
            ]
            if part
        ),
        limit=1600,
    )
    return {
        "record_id": page_url.rstrip("/").rsplit("/", 1)[-1],
        "title": title or fallback.get("title", ""),
        "subject": subject or fallback.get("subject", ""),
        "description": description or fallback.get("description", ""),
        "date": _extract_year(detail_text) or fallback.get("date", ""),
        "duration": _extract_duration(detail_text) or fallback.get("duration", ""),
        "page_url": page_url,
        "media_url": media_url,
        "program_label": fallback.get("program_label", "Selects"),
        "embedded": bool(media_url),
    }


def collect_deutsche_kinemathek_institutions():
    return [
        {
            "institution": DEUTSCHE_KINEMATHEK_INSTITUTION_NAME,
            "slug": slugify("deutsche-kinemathek-museum-fuer-film-und-fernsehen"),
            "country": DEUTSCHE_KINEMATHEK_COUNTRY,
            "continent": country_to_continent(DEUTSCHE_KINEMATHEK_COUNTRY),
            "repository_code": DEUTSCHE_KINEMATHEK_REPOSITORY_CODE,
            "archive_type": DEUTSCHE_KINEMATHEK_ARCHIVE_TYPE,
            "deutsche_kinemathek_detail_url": DEUTSCHE_KINEMATHEK_STREAMING_URL,
            "external_url": DEUTSCHE_KINEMATHEK_HOME_URL,
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
        "repository_code": DEUTSCHE_KINEMATHEK_REPOSITORY_CODE,
        "archive_type": DEUTSCHE_KINEMATHEK_ARCHIVE_TYPE,
        "deutsche_kinemathek_detail_url": DEUTSCHE_KINEMATHEK_STREAMING_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": DEUTSCHE_KINEMATHEK_STREAMING_URL,
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
        "partner_site": DEUTSCHE_KINEMATHEK_STREAMING_URL,
        "platform": DEUTSCHE_KINEMATHEK_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_deutsche_kinemathek_dataset():
    institutions = collect_deutsche_kinemathek_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_url = {}

    for url, warning in [
        (DEUTSCHE_KINEMATHEK_HOME_URL, "Site institucional da Deutsche Kinemathek."),
        (DEUTSCHE_KINEMATHEK_FILM_ARCHIVE_URL, "Página institucional do Film Archive."),
        (DEUTSCHE_KINEMATHEK_DIGITAL_COLLECTION_URL, "Página institucional da coleção digital e portal de busca."),
        (DEUTSCHE_KINEMATHEK_SEARCH_PORTAL_URL, "Portal de busca público; aplicação JavaScript, usado como contexto, não como rota MVP de streaming."),
        (DEUTSCHE_KINEMATHEK_STREAMING_URL, "Página pública do programa Selects em streaming."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    try:
        response = _fetch(DEUTSCHE_KINEMATHEK_STREAMING_URL)
        listed_records = parse_deutsche_kinemathek_streaming_page(response.text, response.url)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(listed_records),
                sum(1 for record in listed_records if record.get("embedded")),
                "Listagem pública Selects materializada por cards de filme com tags video/source.",
            )
        )
    except Exception as error:
        listed_records = []
        errors.append(f"{DEUTSCHE_KINEMATHEK_STREAMING_URL}: {error}")
        internal_pages.append(_internal_page_row(institution, DEUTSCHE_KINEMATHEK_STREAMING_URL, "erro", warning="Falha ao abrir o programa Selects.", error=str(error)))

    for listed_record in listed_records:
        detail_url = listed_record["page_url"]
        try:
            response = _fetch(detail_url)
            record = parse_deutsche_kinemathek_detail_page(response.text, response.url, listed_record)
            records_by_url[response.url] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    1 if record.get("embedded") else 0,
                    "Ficha pública Selects verificada com metadados de filme e sinal de player.",
                )
            )
        except Exception as error:
            errors.append(f"{detail_url}: {error}")
            records_by_url.setdefault(detail_url, listed_record)
            internal_pages.append(_internal_page_row(institution, detail_url, "erro", 0, 1, 1 if listed_record.get("embedded") else 0, "Falha ao abrir ficha; registro mantido pela listagem pública Selects.", str(error)))
        time.sleep(DEUTSCHE_KINEMATHEK_REQUEST_PAUSE)

    records = list(records_by_url.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("page_url")]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": DEUTSCHE_KINEMATHEK_STREAMING_URL,
            "partner_domain": normalize_domain(DEUTSCHE_KINEMATHEK_STREAMING_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": DEUTSCHE_KINEMATHEK_STREAMING_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if video_links else "alta",
            "warning": (
                "Corpus Deutsche Kinemathek incorporado pela rota pública Selects. "
                f"O MVP materializa {len(video_links)} filmes do programa vigente, com {embedded_total} sinais de player. "
                "A coleta não representa o Film Archive integral, não esgota o portal de busca e não baixa mídia."
            ),
            "error": "; ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "DEUTSCHE_KINEMATHEK_ARCHIVE_TYPE",
    "DEUTSCHE_KINEMATHEK_INSTITUTION_NAME",
    "DEUTSCHE_KINEMATHEK_PLATFORM_LABEL",
    "DEUTSCHE_KINEMATHEK_REPOSITORY_CODE",
    "collect_deutsche_kinemathek_dataset",
    "collect_deutsche_kinemathek_institutions",
    "parse_deutsche_kinemathek_detail_page",
    "parse_deutsche_kinemathek_streaming_page",
]
