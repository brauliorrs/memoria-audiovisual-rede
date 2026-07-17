from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import requests

from .config import (
    FILMOTECA_ESPANOLA_API_URL,
    FILMOTECA_ESPANOLA_HOME_URL,
    FILMOTECA_ESPANOLA_PLATFO_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain
from .geography import country_to_continent, normalize_country


FILMOTECA_ESPANOLA_INSTITUTION_NAME = "Filmoteca Española"
FILMOTECA_ESPANOLA_REPOSITORY_CODE = "ES-FILMOTECA-ESPANOLA"
FILMOTECA_ESPANOLA_SLUG = "filmoteca-espanola"
FILMOTECA_ESPANOLA_ARCHIVE_TYPE = (
    "National film archive with public PLATFO FILMO metadata and registration-gated streaming"
)
FILMOTECA_ESPANOLA_COUNTRY = normalize_country("Spain")
FILMOTECA_ESPANOLA_PLATFORM_LABEL = "PLATFO FILMO"
FILMOTECA_ESPANOLA_RIGHTS_HOLDER = "Filmoteca Española"
FILMOTECA_ESPANOLA_MIN_VIDEO_TOTAL = 300

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8,pt-BR;q=0.7",
        "Origin": "https://filmo.platfo.es",
        "Referer": FILMOTECA_ESPANOLA_PLATFO_URL,
        "language": "es",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _api_url(path, **params):
    query = urlencode({key: value for key, value in params.items() if value not in {"", None}})
    return f"{FILMOTECA_ESPANOLA_API_URL}{path}" + (f"?{query}" if query else "")


def _fetch_json(url):
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    return response.json(), response.url, response.status_code


def _walk_videos(payload):
    videos = {}

    def visit(value):
        if isinstance(value, dict):
            is_video = value.get("itemType") == "Video" or (
                value.get("_id") and value.get("slug") and value.get("title") and "duration" in value
            )
            if is_video:
                videos.setdefault(str(value.get("_id") or value.get("slug")), value)
            for key in ("videos", "subcontainers", "heroBanner", "featured"):
                nested = value.get(key)
                if isinstance(nested, list):
                    for item in nested:
                        visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(payload)
    return videos


def _layout_items(video, key):
    layout = video.get("layout") or {}
    value = layout.get(key) or []
    return value if isinstance(value, list) else []


def _join_values(items, *, title=None):
    values = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if title and item.get("title") != title:
            continue
        value = _clean_text(item.get("value") or item.get("name") or item.get("complete"))
        if value:
            values.append(value)
    return "; ".join(dict.fromkeys(values))


def _other_value(video, title):
    return _join_values(_layout_items(video, "other"), title=title)


def _has_filmoteca_espanola_rights(video):
    return FILMOTECA_ESPANOLA_RIGHTS_HOLDER in _other_value(video, "Titular de los derechos")


def _ms_to_year(value):
    if value in {"", None}:
        return ""
    try:
        date = datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=int(value))
        return str(date.year)
    except (TypeError, ValueError, OverflowError):
        return ""


def _best_thumbnail(video):
    thumbnail = video.get("thumbnail") or {}
    for key in ("landscape", "portrait", "banner"):
        if thumbnail.get(key):
            return thumbnail[key]
    for key in ("landscapes", "portraits", "banners"):
        values = thumbnail.get(key)
        if isinstance(values, list) and values:
            return values[0].get("url", "")
    return ""


def parse_filmoteca_espanola_video(video):
    record_id = str(video.get("_id") or "")
    slug = str(video.get("slug") or "")
    title = _clean_text(video.get("title") or record_id)
    genre = _join_values(_layout_items(video, "genre"))
    subgenre = _join_values(_layout_items(video, "subgenre"))
    topic = _join_values(_layout_items(video, "topic"))
    labels = _join_values(_layout_items(video, "label"), title="Etiqueta") or _join_values(_layout_items(video, "label"))
    country = _other_value(video, "País")
    rights = _other_value(video, "Titular de los derechos")
    collection = _other_value(video, "Colección")
    original_format = _other_value(video, "Formato de la obra original")
    color = _other_value(video, "Tipo de color")
    language = _other_value(video, "Idioma original")
    duration = video.get("duration")
    year = _ms_to_year(video.get("date"))
    video_link = f"https://filmo.platfo.es/content/{slug}" if slug else _api_url(f"/video/{record_id}", version=2)

    subject = "; ".join(
        part
        for part in [
            topic,
            genre,
            subgenre,
            f"país: {country}" if country else "",
            f"colección: {collection}" if collection else "",
            f"etiquetas: {labels}" if labels else "",
        ]
        if part
    )
    description_parts = [
        video.get("shortDescription", ""),
        video.get("description", ""),
        video.get("longDescription", ""),
        f"código PLATFO: {record_id}" if record_id else "",
        f"titular de derechos: {rights}" if rights else "",
        f"formato original: {original_format}" if original_format else "",
        f"color: {color}" if color else "",
        f"idioma original: {language}" if language else "",
        f"duración declarada: {duration} segundos" if duration not in {"", None} else "",
        "regime de acesso PLATFO: login/cadastro obrigatório; metadados públicos, mídia não baixada.",
    ]
    return {
        "record_id": record_id,
        "slug": slug,
        "video_link": video_link,
        "title": title,
        "subject": _clean_text(subject, limit=900),
        "description": _clean_text(" | ".join(part for part in description_parts if _clean_text(part)), limit=1800),
        "date": year,
        "rights_holder": rights,
        "collection": collection,
        "thumbnail": _best_thumbnail(video),
        "access": _clean_text(video.get("access", "")),
    }


def _find_filmoteca_espanola_rights_id(filters_payload):
    for item in filters_payload or []:
        if item.get("param") != "copyright":
            continue
        for value in item.get("values") or []:
            if value.get("name") == FILMOTECA_ESPANOLA_RIGHTS_HOLDER:
                return str(value.get("_id") or "")
    return "23723"


def collect_filmoteca_espanola_institutions():
    return [
        {
            "institution": FILMOTECA_ESPANOLA_INSTITUTION_NAME,
            "slug": FILMOTECA_ESPANOLA_SLUG,
            "country": FILMOTECA_ESPANOLA_COUNTRY,
            "continent": country_to_continent(FILMOTECA_ESPANOLA_COUNTRY),
            "repository_code": FILMOTECA_ESPANOLA_REPOSITORY_CODE,
            "archive_type": FILMOTECA_ESPANOLA_ARCHIVE_TYPE,
            "filmoteca_espanola_detail_url": FILMOTECA_ESPANOLA_HOME_URL,
            "external_url": FILMOTECA_ESPANOLA_PLATFO_URL,
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
        "repository_code": FILMOTECA_ESPANOLA_REPOSITORY_CODE,
        "archive_type": FILMOTECA_ESPANOLA_ARCHIVE_TYPE,
        "filmoteca_espanola_detail_url": FILMOTECA_ESPANOLA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_ESPANOLA_PLATFO_URL,
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
        "partner_site": FILMOTECA_ESPANOLA_PLATFO_URL,
        "platform": FILMOTECA_ESPANOLA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_filmoteca_espanola_dataset(fetch_json=_fetch_json):
    institutions = collect_filmoteca_espanola_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    catalogs_url = _api_url("/catalogs")
    filters_url = _api_url("/search/filters", **{"image-format": "webp"})
    collections_url = _api_url(
        "/container",
        containerType="Collection",
        version=2,
        **{"image-format": "webp", "size": 10000, "page": 1},
    )

    try:
        catalogs_payload, final_url, status = fetch_json(catalogs_url)
        internal_pages.append(
            _internal_page_row(
                institution,
                final_url,
                "ok",
                status,
                count=0,
                warning=f"Catálogos públicos PLATFO detectados: {len(catalogs_payload) if isinstance(catalogs_payload, list) else 0}.",
            )
        )
    except Exception as error:
        errors.append(f"catalogs: {error}")
        internal_pages.append(_internal_page_row(institution, catalogs_url, "erro", error=str(error)))

    try:
        filters_payload, filters_final_url, filters_status = fetch_json(filters_url)
        rights_id = _find_filmoteca_espanola_rights_id(filters_payload)
        internal_pages.append(
            _internal_page_row(
                institution,
                filters_final_url,
                "ok",
                filters_status,
                count=1,
                warning=f"Filtro oficial de titularidade localizado para {FILMOTECA_ESPANOLA_RIGHTS_HOLDER}: {rights_id}.",
            )
        )
    except Exception as error:
        rights_id = "23723"
        errors.append(f"filters: {error}")
        internal_pages.append(_internal_page_row(institution, filters_url, "erro", error=str(error)))

    try:
        collections_payload, collections_final_url, collections_status = fetch_json(collections_url)
        collection_videos = _walk_videos(collections_payload)
        internal_pages.append(
            _internal_page_row(
                institution,
                collections_final_url,
                "ok",
                collections_status,
                count=len(collection_videos),
                warning=(
                    "Rota de coleções PLATFO usada como controle contextual; o corpus individual é filtrado "
                    "por titularidade Filmoteca Española, não pela totalidade da PLATFO."
                ),
            )
        )
    except Exception as error:
        errors.append(f"collections: {error}")
        internal_pages.append(_internal_page_row(institution, collections_url, "erro", error=str(error)))

    search_url = _api_url(
        "/search",
        copyright=rights_id,
        version=2,
        **{"image-format": "webp", "size": 10000, "page": 1},
    )
    try:
        search_payload, search_final_url, search_status = fetch_json(search_url)
        raw_videos = _walk_videos(search_payload)
        parsed_records = [
            parse_filmoteca_espanola_video(video)
            for video in raw_videos.values()
            if _has_filmoteca_espanola_rights(video)
        ]
        internal_pages.append(
            _internal_page_row(
                institution,
                search_final_url,
                "ok",
                search_status,
                count=len(parsed_records),
                warning=(
                    "Busca pública PLATFO por titularidade Filmoteca Española; registros com titularidade divergente "
                    "são descartados no pós-filtro."
                ),
            )
        )
    except Exception as error:
        parsed_records = []
        errors.append(f"search copyright {rights_id}: {error}")
        internal_pages.append(_internal_page_row(institution, search_url, "erro", error=str(error)))

    records = sorted(parsed_records, key=lambda item: (item.get("date", ""), item.get("title", "")))
    rows_video_links = [_record_to_video_row(institution, record) for record in records]
    total_records = len(rows_video_links)
    complete = total_records >= FILMOTECA_ESPANOLA_MIN_VIDEO_TOTAL
    collections = sorted({record.get("collection", "") for record in records if record.get("collection")})
    access_values = sorted({record.get("access", "") for record in records if record.get("access")})
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": FILMOTECA_ESPANOLA_PLATFO_URL,
            "partner_domain": normalize_domain(FILMOTECA_ESPANOLA_PLATFO_URL),
            "status": "ok" if total_records else "sem_video_publico",
            "http_code": "200" if total_records else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": search_url,
            "video_links_found_total": total_records,
            "embedded_video_signals_total": total_records,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": not complete,
            "warning": (
                f"PLATFO materializou {total_records} registros públicos de metadados com titularidade "
                f"{FILMOTECA_ESPANOLA_RIGHTS_HOLDER}. Regime de acesso observado: "
                f"{', '.join(access_values) if access_values else 'não identificado'}. "
                "O corpus representa o recorte público PLATFO FILMO da Filmoteca Española, não a totalidade "
                "do acervo físico, nem registros da PLATFO pertencentes a outros arquivos espanhóis."
                + (f" Coleções declaradas: {', '.join(collections)}." if collections else "")
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, internal_pages


__all__ = [
    "FILMOTECA_ESPANOLA_MIN_VIDEO_TOTAL",
    "FILMOTECA_ESPANOLA_PLATFORM_LABEL",
    "collect_filmoteca_espanola_dataset",
    "collect_filmoteca_espanola_institutions",
    "parse_filmoteca_espanola_video",
]
