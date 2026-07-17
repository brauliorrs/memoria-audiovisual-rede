from __future__ import annotations

import json
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CRNOGORSKA_KINOTEKA_EFG_CONTENT_URL,
    CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL,
    CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
    CRNOGORSKA_KINOTEKA_HOME_URL,
    HEADERS,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CRNOGORSKA_KINOTEKA_REPOSITORY_CODE = "ME-CK"
CRNOGORSKA_KINOTEKA_ARCHIVE_TYPE = "National film archive / cinematheque"
CRNOGORSKA_KINOTEKA_COUNTRY = normalize_country("Montenegro")
CRNOGORSKA_KINOTEKA_INSTITUTION_NAME = "Crnogorska Kinoteka"
CRNOGORSKA_KINOTEKA_PLATFORM_LABEL = "European Film Gateway"

KNOWN_EFG_RECORD = {
    "record_id": "ck::e7b8ca4b11b56d30c9d260216ffb18aa",
    "title": "Non è resurrezione senza morte",
    "detail_url": CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL,
    "external_view_url": "http://kinoteka.me/arhiv/voskrsenje-film.html",
    "subject": "Feature film | World War I | Montenegro | Drama",
    "date": "1922-04-14",
    "description": (
        "Ficha pública da Crnogorska Kinoteka no European Film Gateway. Filme de ficção reconstruído "
        "sobre Montenegro e a Primeira Guerra Mundial, identificado pelo EFG como registro de vídeo "
        "da Crnogorska Kinoteka. A coleta registra metadados e rota pública, sem baixar mídia."
    ),
}

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "da,en;q=0.9,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = SESSION.get(url, timeout=(6, 12), allow_redirects=True)
    response.raise_for_status()
    return response


def _extract_player_source(soup):
    video = soup.find("video")
    if not video or not video.get("data-setup"):
        return ""
    try:
        setup = json.loads(video["data-setup"])
    except Exception:
        return ""
    sources = setup.get("sources") or []
    return _clean_text(sources[0].get("src", "")) if sources else ""


def _extract_external_view_url(soup, page_url):
    for anchor in soup.select("a[href]"):
        label = _clean_text(anchor.get_text(" ", strip=True))
        if label.startswith("View at "):
            return urljoin(page_url, anchor["href"])
    return ""


def collect_crnogorska_kinoteka_institutions():
    return [
        {
            "institution": CRNOGORSKA_KINOTEKA_INSTITUTION_NAME,
            "slug": slugify(CRNOGORSKA_KINOTEKA_INSTITUTION_NAME),
            "country": CRNOGORSKA_KINOTEKA_COUNTRY,
            "continent": country_to_continent(CRNOGORSKA_KINOTEKA_COUNTRY),
            "repository_code": CRNOGORSKA_KINOTEKA_REPOSITORY_CODE,
            "archive_type": CRNOGORSKA_KINOTEKA_ARCHIVE_TYPE,
            "crnogorska_kinoteka_detail_url": CRNOGORSKA_KINOTEKA_EFG_CONTENT_URL,
            "external_url": CRNOGORSKA_KINOTEKA_HOME_URL,
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
        "repository_code": CRNOGORSKA_KINOTEKA_REPOSITORY_CODE,
        "archive_type": CRNOGORSKA_KINOTEKA_ARCHIVE_TYPE,
        "crnogorska_kinoteka_detail_url": CRNOGORSKA_KINOTEKA_EFG_CONTENT_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_crnogorska_kinoteka_detail_page(html, page_url=CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    title = _clean_text((soup.find("h1") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    text = _clean_text(soup.get_text(" ", strip=True), limit=1400)
    media_source_url = _extract_player_source(soup)
    external_view_url = _extract_external_view_url(soup, page_url)
    has_player_shell = "video-js" in str(html or "").lower() or "supports html5 video" in text.lower()
    description = _clean_text(
        " | ".join(
            value
            for value in [
                KNOWN_EFG_RECORD["description"],
                "player EFG sinalizado no HTML, sem fonte de mídia materializada na coleta estática"
                if has_player_shell and not media_source_url
                else "",
                f"fonte de mídia: {media_source_url}" if media_source_url else "",
                f"ver também: {external_view_url}" if external_view_url else KNOWN_EFG_RECORD["external_view_url"],
                text,
            ]
            if value
        ),
        limit=1400,
    )
    return {
        **KNOWN_EFG_RECORD,
        "title": title or KNOWN_EFG_RECORD["title"],
        "detail_url": page_url,
        "media_source_url": media_source_url,
        "external_view_url": external_view_url or KNOWN_EFG_RECORD["external_view_url"],
        "description": description,
        "has_player_shell": has_player_shell,
        "detail_fetch_status": "ok",
    }


def _fallback_record(error):
    return {
        **KNOWN_EFG_RECORD,
        "media_source_url": "",
        "has_player_shell": False,
        "detail_fetch_status": "fallback_indice_publico",
        "description": _clean_text(
            f"{KNOWN_EFG_RECORD['description']} A ficha EFG não abriu nesta rodada automática ({error}); "
            "o registro permanece por evidência pública indexada pelo EFG e deve ser retestado no ciclo mensal.",
            limit=1000,
        ),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
        "platform": CRNOGORSKA_KINOTEKA_PLATFORM_LABEL,
        "video_link": record.get("detail_url", CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_crnogorska_kinoteka_dataset():
    institutions = collect_crnogorska_kinoteka_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    for url, warning in [
        (CRNOGORSKA_KINOTEKA_EFG_CONTENT_URL, "Página da Crnogorska Kinoteka como arquivo contribuinte no EFG."),
        (CRNOGORSKA_KINOTEKA_HOME_URL, "Site institucional; indisponibilidade não bloqueia a ficha pública EFG."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    try:
        response = _fetch(CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL)
        record = parse_crnogorska_kinoteka_detail_page(response.text, response.url)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                1,
                int(record.get("has_player_shell", False)),
                "Ficha pública de vídeo CK no European Film Gateway.",
            )
        )
    except Exception as error:
        errors.append(f"{CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL}: {error}")
        record = _fallback_record(error)
        internal_pages.append(
            _internal_page_row(
                institution,
                CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL,
                "erro",
                video_count=1,
                warning="Ficha CK identificada publicamente no EFG, mas rota oscilou na rodada automática.",
                error=str(error),
            )
        )

    video_links = [_record_to_video_row(institution, record)]
    integrity_status = "acessivel" if record.get("detail_fetch_status") == "ok" else "instavel"
    summary = [
        {
            **_base_row(institution),
            "partner_site": CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL,
            "partner_domain": normalize_domain(CRNOGORSKA_KINOTEKA_EFG_SEARCH_URL),
            "status": "ok",
            "http_code": 200 if record.get("detail_fetch_status") == "ok" else "",
            "integrity_status": integrity_status,
            "final_url": CRNOGORSKA_KINOTEKA_EFG_DETAIL_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": int(record.get("has_player_shell", False)),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if integrity_status == "acessivel" else "media",
            "warning": (
                "Corpus institucional incorporado pelo recorte público da Crnogorska Kinoteka no EFG. "
                "A unidade custodial é a Crnogorska Kinoteka; o EFG é a superfície agregadora de acesso. "
                "A rodada registra uma ficha de vídeo pública e não baixa mídia."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CRNOGORSKA_KINOTEKA_ARCHIVE_TYPE",
    "CRNOGORSKA_KINOTEKA_INSTITUTION_NAME",
    "CRNOGORSKA_KINOTEKA_PLATFORM_LABEL",
    "CRNOGORSKA_KINOTEKA_REPOSITORY_CODE",
    "KNOWN_EFG_RECORD",
    "collect_crnogorska_kinoteka_dataset",
    "collect_crnogorska_kinoteka_institutions",
    "parse_crnogorska_kinoteka_detail_page",
]
