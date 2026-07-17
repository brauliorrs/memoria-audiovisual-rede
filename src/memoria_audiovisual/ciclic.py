import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CICLIC_FILMS_AJAX_URL,
    CICLIC_FILMS_ARCHIVES_URL,
    CICLIC_HOME_URL,
    CICLIC_MEMOIRE_HOME_URL,
    CICLIC_WEB_MISSION_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CICLIC_REPOSITORY_CODE = "FR-CICLIC"
CICLIC_ARCHIVE_TYPE = "Institutional film and audiovisual archive"
CICLIC_COUNTRY = normalize_country("France")
CICLIC_INSTITUTION_NAME = "CICLIC - Centre-Val-de-Loire"
CICLIC_PLATFORM_LABEL = "Ciclic Mémoire"
CICLIC_MAX_LIST_PAGES = 2
CICLIC_REQUEST_PAUSE = 0.1

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _absolute_url(url):
    return urljoin(CICLIC_MEMOIRE_HOME_URL, str(url or ""))


def _as_int(value, default=0):
    normalized = re.sub(r"\D+", "", str(value or ""))
    try:
        return int(normalized)
    except ValueError:
        return default


def collect_ciclic_institutions():
    return [
        {
            "institution": CICLIC_INSTITUTION_NAME,
            "slug": slugify(CICLIC_INSTITUTION_NAME),
            "country": CICLIC_COUNTRY,
            "continent": country_to_continent(CICLIC_COUNTRY),
            "repository_code": CICLIC_REPOSITORY_CODE,
            "archive_type": CICLIC_ARCHIVE_TYPE,
            "ciclic_detail_url": CICLIC_MEMOIRE_HOME_URL,
            "external_url": CICLIC_MEMOIRE_HOME_URL,
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
        "repository_code": CICLIC_REPOSITORY_CODE,
        "archive_type": CICLIC_ARCHIVE_TYPE,
        "ciclic_detail_url": CICLIC_MEMOIRE_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CICLIC_FILMS_ARCHIVES_URL,
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
        "partner_site": CICLIC_FILMS_ARCHIVES_URL,
        "platform": record.get("platform", CICLIC_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _extract_ajax_html(payload):
    if isinstance(payload, list):
        return "\n".join(
            command.get("data", "")
            for command in payload
            if isinstance(command, dict) and isinstance(command.get("data"), str)
        )
    return str(payload or "")


def _fetch_list_page(page):
    response = _fetch(
        CICLIC_FILMS_AJAX_URL,
        params={
            "ajax": "1",
            "useAjax": "1",
            "page": page,
            "vue": "mosaique",
            "uniqID": "ciclic_memoire_liste_films",
            "order": "created/desc",
            "renderMode": "replace" if page == 0 else "addmore",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    response.raise_for_status()
    try:
        return response.url, _extract_ajax_html(response.json()), response.status_code
    except Exception:
        return response.url, response.text, response.status_code


def _parse_declared_total(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    total_text = " ".join(item.get_text(" ", strip=True) for item in soup.select(".node-liste-total"))
    match = re.search(r"(\d[\d\s]*)\s+films", total_text)
    return _as_int(match.group(1)) if match else 0


def parse_ciclic_list_page(html_text, page_number=0):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for item in soup.select("#afficher_plusciclic_memoire_liste_films .block-item, .node-liste .block-item"):
        link = item.find("a", href=True)
        if not link:
            continue
        page_url = _absolute_url(link.get("href"))
        match = re.search(r"/(\d+)-", page_url)
        if not match:
            continue
        record_id = match.group(1)
        if record_id in seen:
            continue
        seen.add(record_id)
        records.append(
            {
                "record_id": record_id,
                "page_url": page_url,
                "list_text": _clean_text(item.get_text(" ", strip=True), limit=500),
                "page_number": page_number,
            }
        )
    return records


def _extract_embed_url(soup):
    for iframe in soup.find_all("iframe", src=True):
        src = iframe.get("src", "")
        if "/embed/" in src:
            return _absolute_url(src)
    return ""


def _extract_video_source(embed_html):
    soup = BeautifulSoup(embed_html or "", "html.parser")
    sources = [source.get("src", "") for source in soup.find_all("source", src=True)]
    for source in sources:
        if source.endswith(".m3u8") or ".m3u8" in source:
            return source, "application/x-mpegURL"
    for source in sources:
        if source.endswith(".mpd") or ".mpd" in source:
            return source, "application/dash+xml"
    for source in sources:
        if source:
            return source, ""
    return "", ""


def _extract_header_values(soup):
    title = _clean_text((soup.find("h1") or soup.find("title") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    title = re.sub(r"\s*\|\s*Ciclic\s*$", "", title).strip()
    header_node = soup.select_one(".node-film-header-infos") or soup.select_one(".node-film-header")
    header_parts = []
    if header_node:
        header_parts = [
            _clean_text(part)
            for part in header_node.get_text(" | ", strip=True).split("|")
            if _clean_text(part)
        ]
    header_text = _clean_text(" | ".join(header_parts))
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", header_text)
    director = ""
    published = ""
    location = ""
    for index, part in enumerate(header_parts):
        if part.startswith("Réalisé par"):
            director = _clean_text(part.split(":", 1)[1] if ":" in part else "")
            if not director and index + 1 < len(header_parts):
                director = header_parts[index + 1]
        if part.startswith("En ligne le"):
            published = _clean_text(part.replace("En ligne le", "", 1))
            if index + 1 < len(header_parts):
                location = header_parts[index + 1]
    if not director:
        director_match = re.search(r"Réalisé par\s*:\s*(.*?)(?:\s+En ligne le|$)", header_text)
        director = _clean_text(director_match.group(1)) if director_match else ""
    if not published:
        published_match = re.search(r"En ligne le\s+(\d{1,2}\s+\w+\s+\d{4})", header_text)
        published = _clean_text(published_match.group(1)) if published_match else ""
    if not location and published:
        location_text = header_text.split(published, 1)[-1]
        location = _clean_text(location_text.split("|", 1)[0])
    return {
        "title": title,
        "year": year_match.group(1) if year_match else "",
        "director": director,
        "published": published,
        "location": location,
    }


def _extract_article_description(soup):
    article = soup.find("article") or soup.find("main") or soup
    for tag in article.find_all(["script", "style", "nav", "header", "footer", "iframe", "form"]):
        tag.decompose()
    text = article.get_text(" ", strip=True)
    for marker in ["Partager / intégrer", "Commentaires", "Ajouter un commentaire", "Dernière publication"]:
        if marker in text:
            text = text.split(marker, 1)[0]
    return _clean_text(text, limit=1200)


def parse_ciclic_film_page(html_text, page_url="", embed_html=""):
    soup = BeautifulSoup(html_text or "", "html.parser")
    header = _extract_header_values(soup)
    embed_url = _extract_embed_url(soup)
    video_source, video_type = _extract_video_source(embed_html)
    record_id_match = re.search(r"/(\d+)-", page_url or "")
    record_id = record_id_match.group(1) if record_id_match else ""
    description = _extract_article_description(soup)
    subject_parts = [
        header.get("director", ""),
        header.get("location", ""),
    ]
    note = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do catálogo Ciclic Mémoire.",
                f"realização: {header.get('director')}" if header.get("director") else "",
                f"local: {header.get('location')}" if header.get("location") else "",
                f"embed: {embed_url}" if embed_url else "",
                f"fonte de vídeo: {video_type}" if video_type else "",
                description,
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": record_id,
        "source_kind": "ciclic_memoire_film",
        "video_link": video_source or embed_url or page_url,
        "page_url": page_url,
        "platform": CICLIC_PLATFORM_LABEL,
        "title": header.get("title", ""),
        "subject": "; ".join(value for value in subject_parts if value),
        "description": note,
        "date": header.get("year", "") or header.get("published", ""),
        "embedded": bool(video_source or embed_url),
    }


def collect_ciclic_dataset():
    institutions = collect_ciclic_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_total = 0

    for url, warning in [
        (CICLIC_HOME_URL, "Site institucional CICLIC."),
        (CICLIC_MEMOIRE_HOME_URL, "Site Ciclic Mémoire, superfície pública do acervo audiovisual."),
        (CICLIC_WEB_MISSION_URL, "Página institucional sobre difusão dos filmes na web."),
        (CICLIC_FILMS_ARCHIVES_URL, "Listagem pública `Films d'archives`, usada como rota de coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(CICLIC_MAX_LIST_PAGES):
        try:
            page_url, page_html, status_code = _fetch_list_page(page)
            if page == 0:
                declared_total = _parse_declared_total(page_html)
            listed_records = parse_ciclic_list_page(page_html, page)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "ok",
                    status_code,
                    len(listed_records),
                    0,
                    f"Página AJAX {page + 1} de listagem pública Ciclic Mémoire.",
                )
            )
        except Exception as error:
            errors.append(f"list page {page}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{CICLIC_FILMS_AJAX_URL}?page={page}",
                    "erro",
                    warning="Falha ao abrir página AJAX da listagem pública Ciclic Mémoire.",
                    error=str(error),
                )
            )
            continue

        for listed_record in listed_records:
            record_id = listed_record["record_id"]
            if record_id in records_by_id:
                continue
            detail_html = ""
            embed_html = ""
            embed_url = ""
            try:
                detail_response = _fetch(listed_record["page_url"])
                detail_response.raise_for_status()
                detail_html = detail_response.text
                detail_soup = BeautifulSoup(detail_html, "html.parser")
                embed_url = _extract_embed_url(detail_soup)
                if embed_url:
                    try:
                        embed_response = _fetch(embed_url)
                        embed_response.raise_for_status()
                        embed_html = embed_response.text
                    except Exception as error:
                        errors.append(f"{embed_url}: {error}")
                parsed = parse_ciclic_film_page(detail_html, detail_response.url, embed_html)
                records_by_id[record_id] = {**listed_record, **parsed}
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        detail_response.url,
                        "ok",
                        detail_response.status_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública Ciclic Mémoire verificada, com embed registrado sem baixar mídia.",
                    )
                )
            except Exception as error:
                errors.append(f"{listed_record['page_url']}: {error}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        listed_record["page_url"],
                        "erro",
                        warning="Falha ao abrir ficha pública Ciclic Mémoire.",
                        error=str(error),
                    )
                )
            time.sleep(CICLIC_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CICLIC_FILMS_ARCHIVES_URL,
            "partner_domain": normalize_domain(CICLIC_FILMS_ARCHIVES_URL),
            "status": "ok" if records else "erro",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "instavel",
            "final_url": CICLIC_FILMS_ARCHIVES_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado por listagem AJAX pública `Films d'archives`. "
                f"A página declarou {declared_total or 'milhares de'} filmes; o MVP materializa "
                f"{len(records)} registros nas primeiras {CICLIC_MAX_LIST_PAGES} páginas da listagem pública, "
                "sem baixar mídia e sem afirmar catálogo total."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CICLIC_ARCHIVE_TYPE",
    "CICLIC_COUNTRY",
    "CICLIC_INSTITUTION_NAME",
    "CICLIC_MAX_LIST_PAGES",
    "CICLIC_PLATFORM_LABEL",
    "CICLIC_REPOSITORY_CODE",
    "collect_ciclic_dataset",
    "collect_ciclic_institutions",
    "parse_ciclic_film_page",
    "parse_ciclic_list_page",
]
