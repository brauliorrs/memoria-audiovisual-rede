from __future__ import annotations

import json
import re

import requests

from .config import (
    ARKAADER_BROADCASTS_API_URL,
    ARKAADER_FILM_SHELF_URL,
    ARKAADER_HOME_URL,
    ARKAADER_MOVIES_JSON_URL,
    ARKAADER_PROJECT_SLUG,
    ESTONIAN_FILM_ARCHIVE_FILM_PAGE_URL,
    ESTONIAN_FILM_ARCHIVE_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ESTONIAN_FILM_ARCHIVE_REPOSITORY_CODE = "EE-RA-EFA"
ESTONIAN_FILM_ARCHIVE_ARCHIVE_TYPE = "National film archive with public audiovisual streaming catalogue"
ESTONIAN_FILM_ARCHIVE_COUNTRY = normalize_country("Estonia")
ESTONIAN_FILM_ARCHIVE_INSTITUTION_NAME = "Film Archive of the National Archives of Estonia"
ESTONIAN_FILM_ARCHIVE_PLATFORM_LABEL = "Arkaader"
ARKAADER_CLIENT_ID = 8480
ARKAADER_EXPECTED_MOVIE_TOTAL = 3980
ARKAADER_EXPECTED_BROADCAST_TOTAL = 3841
ARKAADER_MIN_MOVIE_TOTAL = 3900
ARKAADER_MIN_BROADCAST_TOTAL = 3800

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json,text/html,*/*",
        "Accept-Language": "en,et;q=0.9,pt-BR;q=0.7",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    text = _clean_text(value)
    return [text] if text else []


def _field_value(fields, key):
    value = fields.get(key, {})
    return value.get("value") if isinstance(value, dict) else value


def _duration_text(seconds):
    try:
        seconds = int(seconds or 0)
    except (TypeError, ValueError):
        return ""
    if not seconds:
        return ""
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}" if hour else f"{minute:02d}:{second:02d}"


def _arkaader_url(token):
    token = _clean_text(token)
    return f"{ARKAADER_HOME_URL.rstrip('/')}/landing/bc/{ARKAADER_PROJECT_SLUG}/{token}" if token else ""


def _access_label(broadcast):
    if broadcast.get("geoRestricted"):
        return "acesso com restrição territorial"
    if broadcast.get("ticketRestricted"):
        return "acesso pago ou por ingresso"
    return "acesso público gratuito"


def _price_label(broadcast):
    prices = broadcast.get("price") or []
    values = []
    for price in prices:
        try:
            values.append(f"{float(price):.2f} EUR")
        except (TypeError, ValueError):
            continue
    return ", ".join(values)


def _link_summary(fields):
    links = _field_value(fields, "links") or []
    summaries = []
    for link in links:
        if not isinstance(link, dict):
            continue
        name = _clean_text(link.get("name"))
        url = _clean_text(link.get("link"))
        if name and url:
            summaries.append(f"{name}: {url}")
    return "; ".join(summaries[:4])


def parse_arkaader_movies_payload(payload):
    records = {}
    for item in payload or []:
        record_id = _clean_text(item.get("_ref"))
        fields = (item.get("data") or {}).get("fields") or {}
        if record_id and fields:
            records[record_id] = fields
    return records


def parse_arkaader_broadcasts_payload(payload, movie_fields_by_ref):
    records = []
    for broadcast in payload or []:
        record_id = _clean_text(broadcast.get("vl2id"))
        token = _clean_text(broadcast.get("token"))
        if not record_id or not token:
            continue
        fields = movie_fields_by_ref.get(record_id, {})
        metadata = {}
        try:
            metadata = json.loads(broadcast.get("metadata") or "{}")
        except (TypeError, ValueError):
            metadata = {}
        title = _clean_text(_field_value(fields, "name") or metadata.get("title"), limit=300)
        film_types = _as_list(_field_value(fields, "filmType"))
        genres = _as_list(_field_value(fields, "genre"))
        directors = _as_list(_field_value(fields, "director") or metadata.get("director"))
        year = _clean_text(_field_value(fields, "year") or metadata.get("year"))
        duration = _duration_text(_field_value(fields, "duration") or metadata.get("duration"))
        introduction = _clean_text(_field_value(fields, "introduction"))
        description = _clean_text(_field_value(fields, "description"))
        price = _price_label(broadcast)
        access = _access_label(broadcast)
        subject = "; ".join([*film_types, *genres, *directors[:2]])
        description_parts = [
            description,
            introduction,
            f"tipo de filme: {', '.join(film_types)}" if film_types else "",
            f"gênero: {', '.join(genres)}" if genres else "",
            f"direção: {', '.join(directors)}" if directors else "",
            f"ano: {year}" if year else "",
            f"duração: {duration}" if duration else "",
            f"regime Arkaader: {access}",
            f"preço declarado: {price}" if price else "",
            "georrestrição declarada" if broadcast.get("geoRestricted") else "",
            f"referências externas: {_link_summary(fields)}" if _link_summary(fields) else "",
            "transmissão pública detectada pela API /api/broadcasts do Arkaader; mídia não baixada.",
        ]
        records.append(
            {
                "record_id": record_id,
                "token": token,
                "video_link": _arkaader_url(token),
                "embed_link": f"{ARKAADER_HOME_URL.rstrip('/')}/embed/{token}",
                "platform": ESTONIAN_FILM_ARCHIVE_PLATFORM_LABEL,
                "title": title or record_id,
                "subject": subject,
                "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1600),
                "date": year,
                "film_types": film_types,
                "genres": genres,
                "access": access,
                "is_free": not bool(broadcast.get("ticketRestricted")),
                "is_geo_restricted": bool(broadcast.get("geoRestricted")),
                "thumbnail_url": _clean_text(broadcast.get("image")),
            }
        )
    return records


def _fetch_movies_json():
    response = SESSION.get(ARKAADER_MOVIES_JSON_URL, timeout=(8, REQUEST_TIMEOUT))
    response.raise_for_status()
    return response.json(), response.url, response.status_code


def _fetch_broadcasts_json():
    response = SESSION.post(
        ARKAADER_BROADCASTS_API_URL,
        json={
            "clientId": ARKAADER_CLIENT_ID,
            "fields": ["token", "metadata", "image", "ticketRestricted", "price", "geoRestricted"],
        },
        headers={
            "Content-Type": "application/json",
            "Origin": ARKAADER_HOME_URL.rstrip("/"),
            "Referer": ARKAADER_FILM_SHELF_URL,
        },
        timeout=(8, REQUEST_TIMEOUT),
    )
    response.raise_for_status()
    return response.json(), response.url, response.status_code


def collect_estonian_film_archive_institutions():
    return [
        {
            "institution": ESTONIAN_FILM_ARCHIVE_INSTITUTION_NAME,
            "slug": slugify(ESTONIAN_FILM_ARCHIVE_INSTITUTION_NAME),
            "country": ESTONIAN_FILM_ARCHIVE_COUNTRY,
            "continent": country_to_continent(ESTONIAN_FILM_ARCHIVE_COUNTRY),
            "repository_code": ESTONIAN_FILM_ARCHIVE_REPOSITORY_CODE,
            "archive_type": ESTONIAN_FILM_ARCHIVE_ARCHIVE_TYPE,
            "estonian_film_archive_detail_url": ESTONIAN_FILM_ARCHIVE_FILM_PAGE_URL,
            "external_url": ARKAADER_FILM_SHELF_URL,
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
        "repository_code": ESTONIAN_FILM_ARCHIVE_REPOSITORY_CODE,
        "archive_type": ESTONIAN_FILM_ARCHIVE_ARCHIVE_TYPE,
        "estonian_film_archive_detail_url": ESTONIAN_FILM_ARCHIVE_FILM_PAGE_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ARKAADER_FILM_SHELF_URL,
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
        "partner_site": ARKAADER_FILM_SHELF_URL,
        "platform": record.get("platform", ESTONIAN_FILM_ARCHIVE_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_estonian_film_archive_dataset(fetch_movies=_fetch_movies_json, fetch_broadcasts=_fetch_broadcasts_json):
    institutions = collect_estonian_film_archive_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    movie_fields_by_ref = {}
    broadcasts_payload = []

    try:
        movies_payload, movies_url, movies_status = fetch_movies()
        movie_fields_by_ref = parse_arkaader_movies_payload(movies_payload)
        internal_pages.append(
            _internal_page_row(
                institution,
                movies_url,
                "ok",
                movies_status,
                count=len(movie_fields_by_ref),
                warning="Metadados públicos do Arkaader; nem toda ficha possui transmissão audiovisual pública.",
            )
        )
    except Exception as error:
        errors.append(f"movies.json: {error}")
        internal_pages.append(_internal_page_row(institution, ARKAADER_MOVIES_JSON_URL, "erro", error=str(error)))

    try:
        broadcasts_payload, broadcasts_url, broadcasts_status = fetch_broadcasts()
        internal_pages.append(
            _internal_page_row(
                institution,
                broadcasts_url,
                "ok",
                broadcasts_status,
                count=len(broadcasts_payload),
                warning="API pública de broadcasts do Arkaader com tokens, preços, acesso livre/pago e georrestrição.",
            )
        )
    except Exception as error:
        errors.append(f"api/broadcasts: {error}")
        internal_pages.append(_internal_page_row(institution, ARKAADER_BROADCASTS_API_URL, "erro", error=str(error)))

    records = parse_arkaader_broadcasts_payload(broadcasts_payload, movie_fields_by_ref)
    rows_video_links = [
        _record_to_video_row(institution, record)
        for record in sorted(records, key=lambda item: (item.get("title", ""), item.get("record_id", "")))
    ]
    total_records = len(rows_video_links)
    free_count = sum(1 for record in records if record.get("is_free"))
    paid_count = total_records - free_count
    geo_count = sum(1 for record in records if record.get("is_geo_restricted"))
    metadata_total = len(movie_fields_by_ref)
    complete = total_records >= ARKAADER_MIN_BROADCAST_TOTAL and metadata_total >= ARKAADER_MIN_MOVIE_TOTAL
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": ARKAADER_FILM_SHELF_URL,
            "partner_domain": normalize_domain(ARKAADER_HOME_URL),
            "status": "ok" if total_records else "sem_video_publico",
            "http_code": "200" if total_records else "",
            "integrity_status": "integro" if complete else "acessivel" if total_records else "instavel",
            "final_url": ARKAADER_FILM_SHELF_URL,
            "video_links_found_total": total_records,
            "embedded_video_signals_total": total_records,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": not complete,
            "warning": (
                f"Arkaader expõe {metadata_total} metadados públicos e {total_records} transmissões na API pública. "
                f"Regime detectado: {free_count} gratuitos, {paid_count} pagos/por ingresso, {geo_count} com georrestrição. "
                "A rota ra.ee/Meediateek recusou conexão direta neste ambiente; a incorporação usa a API pública do Arkaader."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, internal_pages


__all__ = [
    "ARKAADER_EXPECTED_BROADCAST_TOTAL",
    "ARKAADER_EXPECTED_MOVIE_TOTAL",
    "ARKAADER_MIN_BROADCAST_TOTAL",
    "ARKAADER_MIN_MOVIE_TOTAL",
    "collect_estonian_film_archive_dataset",
    "collect_estonian_film_archive_institutions",
    "parse_arkaader_broadcasts_payload",
    "parse_arkaader_movies_payload",
]
