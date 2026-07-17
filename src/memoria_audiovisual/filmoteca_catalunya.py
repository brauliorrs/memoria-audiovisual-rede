from __future__ import annotations

from .config import (
    FILMOTECA_CATALUNYA_HOME_URL,
    FILMOTECA_CATALUNYA_PLATFO_URL,
)
from .crawler import normalize_domain
from .filmoteca_espanola import (
    FILMOTECA_ESPANOLA_PLATFORM_LABEL,
    _api_url,
    _fetch_json,
    _other_value,
    _walk_videos,
    parse_filmoteca_espanola_video,
)
from .geography import country_to_continent, normalize_country


FILMOTECA_CATALUNYA_INSTITUTION_NAME = "Filmoteca de Catalunya"
FILMOTECA_CATALUNYA_REPOSITORY_CODE = "ES-CT-FILMOTECA-CATALUNYA"
FILMOTECA_CATALUNYA_SLUG = "filmoteca-catalunya"
FILMOTECA_CATALUNYA_ARCHIVE_TYPE = (
    "Film archive with restricted institutional catalogue and public PLATFO FILMO subset"
)
FILMOTECA_CATALUNYA_COUNTRY = normalize_country("Spain")
FILMOTECA_CATALUNYA_PLATFORM_LABEL = FILMOTECA_ESPANOLA_PLATFORM_LABEL
FILMOTECA_CATALUNYA_RIGHTS_HOLDER = "Filmoteca de Catalunya"
FILMOTECA_CATALUNYA_MIN_VIDEO_TOTAL = 10


def _has_filmoteca_catalunya_rights(video):
    return FILMOTECA_CATALUNYA_RIGHTS_HOLDER in _other_value(video, "Titular de los derechos")


def _find_filmoteca_catalunya_rights_id(filters_payload):
    for item in filters_payload or []:
        if item.get("param") != "copyright":
            continue
        for value in item.get("values") or []:
            if value.get("name") == FILMOTECA_CATALUNYA_RIGHTS_HOLDER:
                return str(value.get("_id") or "")
    return "205985"


def collect_filmoteca_catalunya_institutions():
    return [
        {
            "institution": FILMOTECA_CATALUNYA_INSTITUTION_NAME,
            "slug": FILMOTECA_CATALUNYA_SLUG,
            "country": FILMOTECA_CATALUNYA_COUNTRY,
            "continent": country_to_continent(FILMOTECA_CATALUNYA_COUNTRY),
            "repository_code": FILMOTECA_CATALUNYA_REPOSITORY_CODE,
            "archive_type": FILMOTECA_CATALUNYA_ARCHIVE_TYPE,
            "filmoteca_catalunya_detail_url": FILMOTECA_CATALUNYA_HOME_URL,
            "external_url": FILMOTECA_CATALUNYA_PLATFO_URL,
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
        "repository_code": FILMOTECA_CATALUNYA_REPOSITORY_CODE,
        "archive_type": FILMOTECA_CATALUNYA_ARCHIVE_TYPE,
        "filmoteca_catalunya_detail_url": FILMOTECA_CATALUNYA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FILMOTECA_CATALUNYA_PLATFO_URL,
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
        "partner_site": FILMOTECA_CATALUNYA_PLATFO_URL,
        "platform": FILMOTECA_CATALUNYA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_filmoteca_catalunya_dataset(fetch_json=_fetch_json):
    institutions = collect_filmoteca_catalunya_institutions()
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
        rights_id = _find_filmoteca_catalunya_rights_id(filters_payload)
        internal_pages.append(
            _internal_page_row(
                institution,
                filters_final_url,
                "ok",
                filters_status,
                count=1,
                warning=f"Filtro oficial de titularidade localizado para {FILMOTECA_CATALUNYA_RIGHTS_HOLDER}: {rights_id}.",
            )
        )
    except Exception as error:
        rights_id = "205985"
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
                    "por titularidade Filmoteca de Catalunya, não pela totalidade da PLATFO."
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
            if _has_filmoteca_catalunya_rights(video)
        ]
        internal_pages.append(
            _internal_page_row(
                institution,
                search_final_url,
                "ok",
                search_status,
                count=len(parsed_records),
                warning=(
                    "Busca pública PLATFO por titularidade Filmoteca de Catalunya; registros com titularidade "
                    "divergente são descartados no pós-filtro."
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
    complete = total_records >= FILMOTECA_CATALUNYA_MIN_VIDEO_TOTAL
    access_values = sorted({record.get("access", "") for record in records if record.get("access")})
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": FILMOTECA_CATALUNYA_PLATFO_URL,
            "partner_domain": normalize_domain(FILMOTECA_CATALUNYA_PLATFO_URL),
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
                f"{FILMOTECA_CATALUNYA_RIGHTS_HOLDER}. Regime de acesso observado: "
                f"{', '.join(access_values) if access_values else 'não identificado'}. "
                "O corpus representa o recorte público PLATFO FILMO da Filmoteca de Catalunya, não a totalidade "
                "do acervo físico, nem o catálogo institucional completo, que permanece de acesso restrito/local."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, internal_pages


__all__ = [
    "FILMOTECA_CATALUNYA_MIN_VIDEO_TOTAL",
    "FILMOTECA_CATALUNYA_PLATFORM_LABEL",
    "collect_filmoteca_catalunya_dataset",
    "collect_filmoteca_catalunya_institutions",
]
