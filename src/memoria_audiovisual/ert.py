from __future__ import annotations

import html
import json
import os
import re
import time
import unicodedata
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    ERT_ARCHIVE_HOME_URL,
    ERT_COLLECTIONS_URL,
    ERT_CONTACT_ACCESS_URL,
    ERT_HOME_URL,
    ERT_WP_POSTS_API_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ERT_REPOSITORY_CODE = "GR-ERT"
ERT_ARCHIVE_TYPE = "Public service broadcaster audiovisual archive"
ERT_COUNTRY = normalize_country("Greece")
ERT_INSTITUTION_NAME = "ERT - Hellenic Broadcasting Corporation Archive"
ERT_PLATFORM_LABEL = "ERT Archive"
ERT_PAGE_SIZE = 100
ERT_REQUEST_PAUSE = 0.08
ERT_POST_FIELDS = "id,link,title,content,excerpt,date,categories,tags"
ERT_POST_SUMMARY_FIELDS = "id,link,title,excerpt,date,categories,tags"
ERT_METADATA_LABELS = [
    "Κωδικός Τεκμηρίου",
    "Τύπος ψηφιακού αρχείου",
    "Τίτλος",
    "Χρονολογία Παραγωγής",
    "Ημερομηνία Πρώτης Προβολής",
    "Σκοπός",
    "Είδος",
    "Χαρακτηρισμός",
    "Κατηγορία",
    "Περίληψη",
    "Περιγραφή Περιεχομένου",
]

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "el,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = html.unescape(re.sub(r"\s+", " ", str(value or ""))).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _normalize_for_match(value):
    text = unicodedata.normalize("NFKD", _clean_text(value).lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _rendered(value):
    if isinstance(value, dict):
        return value.get("rendered", "")
    return value or ""


def _plain_text(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    return _clean_text(soup.get_text(" ", strip=True))


def _extract_iframe_sources(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    sources = [tag.get("src", "") for tag in soup.find_all("iframe", src=True)]
    sources += re.findall(r"https?://[^\"'\s<>]+?(?:\.mp4|\.m3u8)(?:[?&][^\"'\s<>]+)?", html_text or "", flags=re.I)
    return list(dict.fromkeys(_clean_text(html.unescape(source)) for source in sources if _clean_text(source)))


def _extract_metadata(text):
    metadata = {}
    label_pattern = "|".join(re.escape(label) for label in ERT_METADATA_LABELS)
    for label in ERT_METADATA_LABELS:
        pattern = rf"{re.escape(label)}\s+(.*?)(?=\s+(?:{label_pattern})\s+|$)"
        match = re.search(pattern, text, flags=re.S)
        if match:
            metadata[label] = _clean_text(match.group(1), limit=1600)
    return metadata


def _extract_date(metadata, post):
    production_year = re.search(r"\b(19\d{2}|20\d{2})\b", metadata.get("Χρονολογία Παραγωγής", ""))
    first_air_date = metadata.get("Ημερομηνία Πρώτης Προβολής", "")
    match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", first_air_date)
    if match:
        day, month, year = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    if production_year:
        return production_year.group(1)
    return str(post.get("date", ""))[:10]


def _is_video_record(metadata, media_sources):
    media_type = _normalize_for_match(metadata.get("Τύπος ψηφιακού αρχείου", ""))
    if "βιντεο" in media_type or "video" in media_type:
        return True
    return any(re.search(r"\.(?:mp4|m3u8)(?:[?&]|$)", source, flags=re.I) for source in media_sources)


def parse_ert_post(post):
    content_html = _rendered(post.get("content"))
    title = _clean_text(_rendered(post.get("title")))
    text = _plain_text(content_html)
    metadata = _extract_metadata(text)
    media_sources = _extract_iframe_sources(content_html)
    if not _is_video_record(metadata, media_sources):
        return None

    record_code = metadata.get("Κωδικός Τεκμηρίου") or str(post.get("id", ""))
    category = metadata.get("Κατηγορία", "")
    genre = metadata.get("Είδος", "")
    purpose = metadata.get("Σκοπός", "")
    summary = metadata.get("Περίληψη") or _clean_text(_plain_text(_rendered(post.get("excerpt"))), limit=800)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                f"Κωδικός Τεκμηρίου: {record_code}" if record_code else "",
                f"Tipo digital declarado: {metadata.get('Τύπος ψηφιακού αρχείου', '')}" if metadata.get("Τύπος ψηφιακού αρχείου") else "",
                f"categoria ERT: {category}" if category else "",
                f"gênero: {genre}" if genre else "",
                f"finalidade: {purpose}" if purpose else "",
                summary,
                "Registro público coletado pela API WordPress do ERT Archive; mídia não baixada.",
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": str(record_code or post.get("id")),
        "source_kind": "ert_wp_video_post",
        "video_link": post.get("link", ""),
        "page_url": post.get("link", ""),
        "platform": ERT_PLATFORM_LABEL,
        "title": metadata.get("Τίτλος") or title,
        "subject": "; ".join(value for value in [category, genre, purpose] if value),
        "description": description,
        "date": _extract_date(metadata, post),
        "embedded": bool(media_sources),
        "media_sources": media_sources,
        "wp_id": post.get("id", ""),
    }


def collect_ert_institutions():
    return [
        {
            "institution": ERT_INSTITUTION_NAME,
            "slug": slugify("ert-archive"),
            "country": ERT_COUNTRY,
            "continent": country_to_continent(ERT_COUNTRY),
            "repository_code": ERT_REPOSITORY_CODE,
            "archive_type": ERT_ARCHIVE_TYPE,
            "ert_detail_url": ERT_ARCHIVE_HOME_URL,
            "external_url": ERT_ARCHIVE_HOME_URL,
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
        "repository_code": ERT_REPOSITORY_CODE,
        "archive_type": ERT_ARCHIVE_TYPE,
        "ert_detail_url": ERT_ARCHIVE_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ERT_ARCHIVE_HOME_URL,
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
        "partner_site": ERT_ARCHIVE_HOME_URL,
        "platform": record.get("platform", ERT_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _max_pages_from_env():
    value = os.environ.get("ERT_MAX_PAGES", "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def _max_records_from_env():
    value = os.environ.get("ERT_MAX_RECORDS", "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def _decode_json_response(response):
    text = response.content.decode("utf-8", errors="replace")
    return json.loads(text, strict=False)


def _fetch_posts_page(page, *, include_content=True):
    response = SESSION.get(
        ERT_WP_POSTS_API_URL,
        params={
            "per_page": ERT_PAGE_SIZE,
            "page": page,
            "_fields": ERT_POST_FIELDS if include_content else ERT_POST_SUMMARY_FIELDS,
        },
        timeout=(8, REQUEST_TIMEOUT),
    )
    response.raise_for_status()
    return _decode_json_response(response), response.url, response.status_code, int(response.headers.get("X-WP-TotalPages") or 1)


def _fetch_post_html_as_post(post):
    url = post.get("link", "")
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return {
        **post,
        "link": response.url,
        "content": {"rendered": response.text},
    }


def _add_video_records(posts, records_by_id, max_records=None):
    page_records = []
    for post in posts:
        record = parse_ert_post(post)
        if not record:
            continue
        records_by_id.setdefault(record["record_id"] or record["video_link"], record)
        page_records.append(record)
        if max_records and len(records_by_id) >= max_records:
            break
    return page_records


def collect_ert_dataset(max_pages=None, max_records=None):
    institutions = collect_ert_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    fallback_warnings = []
    pages_read = 0
    fallback_pages = 0
    max_pages = max_pages or _max_pages_from_env()
    max_records = max_records or _max_records_from_env()

    contextual_pages = [
        (ERT_ARCHIVE_HOME_URL, "Página oficial do ERT Archive; declara patrimônio audiovisual e exibe registros com vídeo."),
        (ERT_COLLECTIONS_URL, "Página de coleções digitais; a coleta usa apenas o arquivo televisivo e registros com evidência pública de vídeo."),
        (ERT_CONTACT_ACCESS_URL, "Página de acesso/contato; informa solicitação por e-mail para pesquisa e uso de material arquivístico."),
        (ERT_HOME_URL, "Site institucional da ERT."),
    ]
    for url, warning in contextual_pages:
        try:
            response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    total_pages = 1
    while page <= total_pages:
        if max_pages and page > max_pages:
            break
        try:
            posts, page_url, status_code, total_pages = _fetch_posts_page(page)
            page_records = _add_video_records(posts, records_by_id, max_records)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "ok",
                    status_code,
                    len(page_records),
                    sum(1 for record in page_records if record.get("embedded")),
                    f"Página {page} de {total_pages} da API WordPress; entram apenas posts com evidência explícita de vídeo.",
                )
            )
            pages_read += 1
            if max_records and len(records_by_id) >= max_records:
                break
            page += 1
            time.sleep(ERT_REQUEST_PAUSE)
        except json.JSONDecodeError as error:
            fallback_warnings.append(f"página {page}: JSON com conteúdo inválido; fallback HTML público aplicado")
            try:
                summary_posts, page_url, status_code, total_pages = _fetch_posts_page(page, include_content=False)
                html_posts = []
                html_errors = []
                for post in summary_posts:
                    try:
                        html_posts.append(_fetch_post_html_as_post(post))
                    except Exception as html_error:
                        html_errors.append(f"{post.get('link', ERT_WP_POSTS_API_URL)}: {html_error}")
                    time.sleep(ERT_REQUEST_PAUSE)
                page_records = _add_video_records(html_posts, records_by_id, max_records)
                fallback_pages += 1
                pages_read += 1
                if html_errors:
                    errors.append(f"posts page {page} fallback html: {' | '.join(html_errors[:5])}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        page_url,
                        "ok_fallback_html" if not html_errors else "ok_fallback_html_parcial",
                        status_code,
                        len(page_records),
                        sum(1 for record in page_records if record.get("embedded")),
                        (
                            f"Página {page} de {total_pages} recuperada por fallback HTML: "
                            "a API WordPress retornou JSON inválido no campo de conteúdo, "
                            "então cada URL pública foi aberta e submetida à mesma regra de vídeo."
                        ),
                        " | ".join(html_errors[:5]),
                    )
                )
                if max_records and len(records_by_id) >= max_records:
                    break
                page += 1
                time.sleep(ERT_REQUEST_PAUSE)
            except Exception as fallback_error:
                errors.append(f"posts page {page}: {error}; fallback failed: {fallback_error}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        ERT_WP_POSTS_API_URL,
                        "erro",
                        warning="Falha ao consultar página da API WordPress e falha no fallback HTML.",
                        error=f"{error}; fallback failed: {fallback_error}",
                    )
                )
                break
        except Exception as error:
            errors.append(f"posts page {page}: {error}")
            internal_pages.append(_internal_page_row(institution, ERT_WP_POSTS_API_URL, "erro", warning="Falha ao consultar página da API WordPress.", error=str(error)))
            break

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    warning = (
        "Corpus ERT incorporado pela API pública WordPress do ERT Archive. "
        "Coleções sem imagem em movimento ficam fora do escopo da coleta. "
        f"Páginas API lidas: {pages_read} de {total_pages}."
    )
    if fallback_pages:
        warning += f" Páginas recuperadas por fallback HTML público: {fallback_pages}."
    if fallback_warnings:
        warning += " Fallbacks metodológicos: " + " | ".join(fallback_warnings[:5]) + "."
    if max_pages:
        warning += f" Rodada limitada por ERT_MAX_PAGES={max_pages}."
    if max_records:
        warning += f" Rodada limitada por ERT_MAX_RECORDS={max_records}."
    if errors:
        warning += " Erros: " + " | ".join(errors[:5])

    summary = [
        {
            **_base_row(institution),
            "partner_site": ERT_ARCHIVE_HOME_URL,
            "partner_domain": normalize_domain(ERT_ARCHIVE_HOME_URL),
            "status": "ok" if video_links else "sem_video",
            "http_code": 200,
            "integrity_status": "integro" if video_links else "sem_registros",
            "final_url": ERT_ARCHIVE_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": warning,
            "error": " | ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "ERT_ARCHIVE_TYPE",
    "ERT_INSTITUTION_NAME",
    "ERT_PLATFORM_LABEL",
    "ERT_REPOSITORY_CODE",
    "collect_ert_dataset",
    "collect_ert_institutions",
    "parse_ert_post",
]
