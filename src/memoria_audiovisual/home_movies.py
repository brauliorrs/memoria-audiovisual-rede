from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests

from .config import (
    HEADERS,
    HOME_MOVIES_HOME_URL,
    MEMORYSCAPES_ARCHIVE_URL,
    MEMORYSCAPES_CLIPS_API_URL,
    MEMORYSCAPES_PROJECT_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


HOME_MOVIES_INSTITUTION_NAME = "Fondazione Home Movies / Archivio Nazionale del Film di Famiglia"
HOME_MOVIES_REPOSITORY_CODE = "IT-HOME-MOVIES-MEMORYSCAPES"
HOME_MOVIES_ARCHIVE_TYPE = "Home movie and private film archive with public digital platform"
HOME_MOVIES_COUNTRY = normalize_country("Italy")
HOME_MOVIES_PLATFORM_LABEL = "Memoryscapes"
HOME_MOVIES_PAGE_SIZE = 500
HOME_MOVIES_DETAIL_WORKERS = 8
HOME_MOVIES_MIN_VIDEO_TOTAL = 4000

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en,it;q=0.9,pt-BR;q=0.7",
        "Referer": MEMORYSCAPES_ARCHIVE_URL,
    }
)


@dataclass(frozen=True)
class MemoryscapesFetchResult:
    data: object
    status_code: int = 200
    final_url: str = ""
    error: str = ""


def fetch_memoryscapes_json(url, params=None):
    try:
        response = SESSION.get(url, params=params or {}, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        response.raise_for_status()
        return MemoryscapesFetchResult(response.json(), response.status_code, response.url, "")
    except Exception as error:
        return MemoryscapesFetchResult({}, "", url, str(error))


def _fetch_result(value, fallback_url):
    if isinstance(value, MemoryscapesFetchResult):
        return value
    return MemoryscapesFetchResult(value, 200, fallback_url, "")


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _localized(value, preferred="en", *, limit=None):
    if isinstance(value, dict):
        return _clean_text(
            value.get(preferred) or value.get("it") or next((item for item in value.values() if item), ""),
            limit=limit,
        )
    return _clean_text(value, limit=limit)


def _join_unique(values):
    return "; ".join(dict.fromkeys(_clean_text(value) for value in values if _clean_text(value)))


def _keywords(record):
    labels = []
    for item in record.get("keywords_data") or []:
        if isinstance(item, dict):
            labels.append(_localized(item.get("value")))
    return _join_unique(labels)


def _coordinates(record):
    coordinates = ((record.get("position") or {}).get("coordinates") or []) if isinstance(record, dict) else []
    if len(coordinates) >= 2:
        return f"{coordinates[1]}, {coordinates[0]}"
    return ""


def build_home_movies_clip_page_url(record_id):
    return f"https://www.memoryscapes.it/en/clips/{record_id}"


def parse_home_movies_record(record):
    record_id = _clean_text(record.get("id"))
    title = _localized(record.get("title"))
    description = _localized(record.get("description"), limit=900)
    author = _clean_text((record.get("author_data") or {}).get("name"))
    keywords = _keywords(record)
    original_format = _clean_text(record.get("format"))
    archive_code = _clean_text(record.get("archive"))
    city = _clean_text(record.get("city") or record.get("province") or record.get("address"))
    page_url = build_home_movies_clip_page_url(record_id)
    player_url = _clean_text(record.get("url_content"))
    dimensions = record.get("content_metadata") or {}
    dimension_note = ""
    if dimensions.get("width") and dimensions.get("height"):
        dimension_note = f"dimensões: {dimensions.get('width')}x{dimensions.get('height')}"
    description_parts = [
        "Clipe público materializado na plataforma Memoryscapes, vinculada à Fondazione Home Movies.",
        description,
        f"autor/fundo: {author}" if author else "",
        f"arquivo/código: {archive_code}" if archive_code else "",
        f"formato: {original_format}" if original_format else "",
        f"palavras-chave: {keywords}" if keywords else "",
        f"lugar: {city}" if city else "",
        f"coordenadas: {_coordinates(record)}" if _coordinates(record) else "",
        dimension_note,
        f"ficha pública: {page_url}",
    ]
    return {
        "record_id": record_id,
        "video_link": player_url,
        "page_url": page_url,
        "platform": HOME_MOVIES_PLATFORM_LABEL,
        "title": title,
        "subject": _join_unique([keywords, author, original_format, city]),
        "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1600),
        "date": _clean_text(record.get("date_from") or record.get("date") or record.get("date_to")),
        "archive_code": archive_code,
        "has_public_player": bool(player_url),
    }


def collect_home_movies_institutions():
    return [
        {
            "institution": HOME_MOVIES_INSTITUTION_NAME,
            "slug": slugify(HOME_MOVIES_INSTITUTION_NAME),
            "country": HOME_MOVIES_COUNTRY,
            "continent": country_to_continent(HOME_MOVIES_COUNTRY),
            "repository_code": HOME_MOVIES_REPOSITORY_CODE,
            "archive_type": HOME_MOVIES_ARCHIVE_TYPE,
            "home_movies_detail_url": HOME_MOVIES_HOME_URL,
            "external_url": MEMORYSCAPES_ARCHIVE_URL,
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
        "repository_code": HOME_MOVIES_REPOSITORY_CODE,
        "archive_type": HOME_MOVIES_ARCHIVE_TYPE,
        "home_movies_detail_url": HOME_MOVIES_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": MEMORYSCAPES_ARCHIVE_URL,
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
        "partner_site": MEMORYSCAPES_ARCHIVE_URL,
        "platform": record.get("platform", HOME_MOVIES_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record_id, fetch_json):
    url = f"{MEMORYSCAPES_CLIPS_API_URL.rstrip('/')}/{record_id}/"
    result = _fetch_result(fetch_json(url), url)
    if result.error:
        return record_id, {}, result
    return record_id, result.data if isinstance(result.data, dict) else {}, result


def collect_home_movies_dataset(fetch_json=fetch_memoryscapes_json, page_size=HOME_MOVIES_PAGE_SIZE):
    institutions = collect_home_movies_institutions()
    institution = institutions[0]
    internal_pages = []
    list_records = []
    declared_total = 0
    page = 1

    while True:
        params = {"page": page, "page_size": page_size, "lang": "en", "view": "list", "order": "-id"}
        result = _fetch_result(fetch_json(MEMORYSCAPES_CLIPS_API_URL, params=params), MEMORYSCAPES_CLIPS_API_URL)
        payload = result.data if isinstance(result.data, dict) else {}
        records = payload.get("results") or []
        declared_total = declared_total or int(payload.get("total_count") or payload.get("count") or 0)
        internal_pages.append(
            _internal_page_row(
                institution,
                result.final_url or MEMORYSCAPES_CLIPS_API_URL,
                "ok" if not result.error else "erro",
                result.status_code,
                len(records),
                0,
                error=result.error,
            )
        )
        list_records.extend(records)
        if result.error or not payload.get("next"):
            break
        page += 1

    ids = list(dict.fromkeys(_clean_text(record.get("id")) for record in list_records if _clean_text(record.get("id"))))
    detail_errors = []
    parsed_records = []
    with ThreadPoolExecutor(max_workers=HOME_MOVIES_DETAIL_WORKERS) as executor:
        future_map = {executor.submit(_fetch_detail, record_id, fetch_json): record_id for record_id in ids}
        for future in as_completed(future_map):
            record_id, detail, result = future.result()
            if result.error:
                detail_errors.append(f"{record_id}: {result.error}")
                continue
            parsed = parse_home_movies_record(detail)
            if parsed["has_public_player"]:
                parsed_records.append(parsed)

    parsed_records.sort(key=lambda item: item.get("record_id", ""))
    deduped_records = []
    seen_video_links = set()
    for record in parsed_records:
        video_link = record.get("video_link", "")
        if not video_link or video_link in seen_video_links:
            continue
        seen_video_links.add(video_link)
        deduped_records.append(record)
    parsed_records = deduped_records
    video_links = [_record_to_video_row(institution, record) for record in parsed_records]
    warning_parts = [
        f"total declarado pela API: {declared_total}" if declared_total else "",
        f"IDs listados: {len(ids)}",
        f"detalhes sem player público, com erro ou duplicados: {len(ids) - len(parsed_records)}",
    ]
    internal_pages.append(
        _internal_page_row(
            institution,
            f"{MEMORYSCAPES_CLIPS_API_URL}{{id}}/",
            "ok" if not detail_errors else "parcial",
            200 if not detail_errors else "",
            len(parsed_records),
            len(parsed_records),
            warning=_clean_text("; ".join(part for part in warning_parts if part)),
            error=" | ".join(detail_errors[:5]),
        )
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": MEMORYSCAPES_ARCHIVE_URL,
            "partner_domain": normalize_domain(MEMORYSCAPES_ARCHIVE_URL),
            "status": "ok" if video_links else "sem_video_publico_detectado",
            "http_code": 200 if video_links else "",
            "integrity_status": "ok" if not detail_errors else "parcial",
            "final_url": MEMORYSCAPES_PROJECT_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text("; ".join(part for part in warning_parts if part)),
            "error": " | ".join(detail_errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "HOME_MOVIES_MIN_VIDEO_TOTAL",
    "MemoryscapesFetchResult",
    "build_home_movies_clip_page_url",
    "collect_home_movies_dataset",
    "collect_home_movies_institutions",
    "fetch_memoryscapes_json",
    "parse_home_movies_record",
]
