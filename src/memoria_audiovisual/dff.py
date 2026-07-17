from __future__ import annotations

import re
import time
from datetime import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    DFF_FILM_ARCHIVE_URL,
    DFF_FILMPORTAL_INFO_URL,
    DFF_FILMPORTAL_VIDEOS_URL,
    DFF_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


DFF_REPOSITORY_CODE = "DE-DFF"
DFF_ARCHIVE_TYPE = "Film institute and museum with public film portal"
DFF_COUNTRY = normalize_country("Germany")
DFF_INSTITUTION_NAME = "DFF - Deutsches Filminstitut & Filmmuseum"
DFF_PLATFORM_LABEL = "filmportal.de"
DFF_MAX_VIDEO_PAGES = 2
DFF_REQUEST_PAUSE = 0.1

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de,en;q=0.8,pt-BR;q=0.7",
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


def _catalog_page_url(page_index):
    return DFF_FILMPORTAL_VIDEOS_URL if page_index == 0 else f"{DFF_FILMPORTAL_VIDEOS_URL}?page={page_index}"


def _format_german_date(value):
    text = _clean_text(value)
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def parse_dff_video_catalog_page(html, page_url=DFF_FILMPORTAL_VIDEOS_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    text = soup.get_text(" ", strip=True)
    total_match = re.search(r"Insgesamt:\s*([\d.]+)\s+Videos", text)
    declared_total = int(total_match.group(1).replace(".", "")) if total_match else 0
    records_by_url = {}

    for anchor in soup.select('a[href*="/video/"]'):
        href = anchor.get("href", "")
        if "/video/" not in href:
            continue
        video_url = urljoin(page_url, href)
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not title and video_url in records_by_url:
            continue
        records_by_url.setdefault(video_url, {"video_link": video_url, "title": ""})
        if title:
            records_by_url[video_url]["title"] = title

    return {
        "declared_total": declared_total,
        "records": [record for record in records_by_url.values() if record["title"]],
    }


def _extract_labeled_fields(soup):
    fields = {}
    for field in soup.select(".field--label-inline, div.field"):
        label_node = field.select_one(".field__label")
        if not label_node:
            continue
        label = _clean_text(label_node.get_text(" ", strip=True))
        if not label:
            continue
        label_node.extract()
        value = _clean_text(field.get_text(" ", strip=True))
        if value:
            fields[label] = value
    return fields


def _extract_uploaded_and_duration(soup):
    submitted = _clean_text(soup.select_one(".video-submitted-on").get_text(" ", strip=True) if soup.select_one(".video-submitted-on") else "")
    date_match = re.search(r"Eingestellt am:\s*([\d.]+)", submitted)
    duration_match = re.search(r"Länge:\s*([^|]+)$", submitted)
    return {
        "published_at": _format_german_date(date_match.group(1)) if date_match else "",
        "duration": _clean_text(duration_match.group(1)) if duration_match else "",
        "submitted_text": submitted,
    }


def parse_dff_video_detail_page(html, page_url):
    soup = BeautifulSoup(html or "", "html.parser")
    h1 = soup.find("h1")
    page_title = _clean_text(h1.get_text(" ", strip=True) if h1 else "")
    if not page_title and soup.find("title"):
        page_title = _clean_text(soup.find("title").get_text(" ", strip=True).replace("| filmportal.de", ""))

    fields = _extract_labeled_fields(soup)
    submitted = _extract_uploaded_and_duration(soup)
    body = _clean_text(
        " ".join(node.get_text(" ", strip=True) for node in soup.select(".field--name-field-edm-video-body-de, .field--name-field-edm-video-body-en")),
        limit=900,
    )
    related_film = _clean_text(
        " ".join(node.get_text(" ", strip=True) for node in soup.select(".field--name-field-video-ref-movie-ref a")),
    )
    players = []
    for iframe in soup.select("iframe"):
        player_url = _clean_text(iframe.get("src") or iframe.get("data-src"))
        if player_url:
            players.append(player_url)

    subject_parts = [
        fields.get("Kategorie", ""),
        fields.get("Thema", ""),
        related_film,
        fields.get("Regie", ""),
    ]
    description_parts = [
        "Ficha pública de vídeo no filmportal.de, plataforma digital operada pelo DFF; mídia não baixada.",
        f"publicação/duração: {submitted['submitted_text']}" if submitted["submitted_text"] else "",
        f"direção: {fields.get('Regie')}" if fields.get("Regie") else "",
        f"produtora: {fields.get('Produktionsfirma')}" if fields.get("Produktionsfirma") else "",
        f"direitos: {fields.get('Rechtsstatus')}" if fields.get("Rechtsstatus") else "",
        f"fonte: {fields.get('Quelle')}" if fields.get("Quelle") else "",
        f"categoria: {fields.get('Kategorie')}" if fields.get("Kategorie") else "",
        f"tema: {fields.get('Thema')}" if fields.get("Thema") else "",
        f"filme relacionado: {related_film}" if related_film else "",
        f"player incorporado: {players[0]}" if players else "",
        body,
    ]
    return {
        "record_id": page_url.rstrip("/").rsplit("/", 1)[-1],
        "title": page_title,
        "subject": "; ".join(part for part in subject_parts if part),
        "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1400),
        "date": submitted["published_at"],
        "duration": submitted["duration"],
        "page_url": page_url,
        "embedded": bool(players),
        "player_url": players[0] if players else "",
    }


def collect_dff_institutions():
    return [
        {
            "institution": DFF_INSTITUTION_NAME,
            "slug": slugify("dff-deutsches-filminstitut-filmmuseum"),
            "country": DFF_COUNTRY,
            "continent": country_to_continent(DFF_COUNTRY),
            "repository_code": DFF_REPOSITORY_CODE,
            "archive_type": DFF_ARCHIVE_TYPE,
            "dff_detail_url": DFF_FILMPORTAL_VIDEOS_URL,
            "external_url": DFF_HOME_URL,
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
        "repository_code": DFF_REPOSITORY_CODE,
        "archive_type": DFF_ARCHIVE_TYPE,
        "dff_detail_url": DFF_FILMPORTAL_VIDEOS_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": DFF_FILMPORTAL_VIDEOS_URL,
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
        "partner_site": DFF_FILMPORTAL_VIDEOS_URL,
        "platform": DFF_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_dff_dataset():
    institutions = collect_dff_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_url = {}
    declared_total = 0

    for url, warning in [
        (DFF_HOME_URL, "Site institucional do DFF."),
        (DFF_FILM_ARCHIVE_URL, "Página institucional do Film Archive do DFF."),
        (DFF_FILMPORTAL_INFO_URL, "Página do DFF sobre o filmportal.de como infraestrutura digital."),
        (DFF_FILMPORTAL_VIDEOS_URL, "Catálogo público de vídeos do filmportal.de."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    listed_records = []
    for page_index in range(DFF_MAX_VIDEO_PAGES):
        catalog_url = _catalog_page_url(page_index)
        try:
            response = _fetch(catalog_url)
            parsed = parse_dff_video_catalog_page(response.text, response.url)
            declared_total = declared_total or parsed["declared_total"]
            page_records = parsed["records"]
            listed_records.extend(page_records)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    0,
                    f"Página {page_index + 1} da listagem pública filmportal.de; total declarado: {declared_total or 'n/d'} vídeos.",
                )
            )
        except Exception as error:
            errors.append(f"{catalog_url}: {error}")
            internal_pages.append(_internal_page_row(institution, catalog_url, "erro", warning="Falha em página paginada do filmportal.de.", error=str(error)))

    for listed_record in listed_records:
        video_url = listed_record["video_link"]
        if video_url in records_by_url:
            continue
        try:
            response = _fetch(video_url)
            record = parse_dff_video_detail_page(response.text, response.url)
            if not record.get("title"):
                record["title"] = listed_record["title"]
            records_by_url[response.url] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    1 if record.get("embedded") else 0,
                    "Ficha pública de vídeo no filmportal.de verificada com metadados e player incorporado quando disponível.",
                )
            )
        except Exception as error:
            errors.append(f"{video_url}: {error}")
            internal_pages.append(_internal_page_row(institution, video_url, "erro", warning="Falha ao abrir ficha de vídeo no filmportal.de.", error=str(error)))
        time.sleep(DFF_REQUEST_PAUSE)

    records = list(records_by_url.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("page_url")]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": DFF_FILMPORTAL_VIDEOS_URL,
            "partner_domain": normalize_domain(DFF_FILMPORTAL_VIDEOS_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": DFF_FILMPORTAL_VIDEOS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if video_links else "alta",
            "warning": (
                "Corpus institucional incorporado por rota pública do filmportal.de, plataforma digital vinculada ao DFF. "
                f"A interface declarou {declared_total or 'n/d'} vídeos e o MVP materializou {len(video_links)} fichas "
                f"nas primeiras {DFF_MAX_VIDEO_PAGES} páginas da listagem pública. Não é o acervo integral do DFF, "
                "não é o Bestandskatalog completo e não baixa mídia."
            ),
            "error": "; ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "DFF_ARCHIVE_TYPE",
    "DFF_INSTITUTION_NAME",
    "DFF_PLATFORM_LABEL",
    "DFF_REPOSITORY_CODE",
    "collect_dff_dataset",
    "collect_dff_institutions",
    "parse_dff_video_catalog_page",
    "parse_dff_video_detail_page",
]
