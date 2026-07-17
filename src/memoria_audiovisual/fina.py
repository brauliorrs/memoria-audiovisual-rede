from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from .config import (
    FINA_HOME_URL,
    FINA_NINATEKA_API_URL,
    FINA_NINATEKA_URL,
    FINA_VIDEO_LIST_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FINA_INSTITUTION_NAME = "Filmoteka Narodowa - Instytut Audiowizualny"
FINA_REPOSITORY_CODE = "PL-FINA"
FINA_ARCHIVE_TYPE = "National film and audiovisual archive with public Ninateka VOD platform"
FINA_COUNTRY = normalize_country("Poland")
FINA_PLATFORM_LABEL = "Ninateka"
FINA_VIDEO_CATEGORY_ID = 1
FINA_PAGE_SIZE = 500
FINA_DETAIL_WORKERS = 6
FINA_MIN_VIDEO_TOTAL = 2500

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8,pt-BR;q=0.7",
        "Referer": FINA_VIDEO_LIST_URL,
    }
)


def _clean_text(value, *, limit=None):
    text = BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _join_names(values):
    if not isinstance(values, list):
        return ""
    names = []
    for item in values:
        value = item.get("name", item) if isinstance(item, dict) else item
        if _clean_text(value):
            names.append(_clean_text(value))
    return "; ".join(names)


def _first_image_url(item):
    images = item.get("images") or item.get("artworks") or {}
    for entries in images.values():
        if isinstance(entries, list) and entries:
            url = str(entries[0].get("url", "")).strip()
            return f"https:{url}" if url.startswith("//") else url
    return ""


def _people_names(persons, roles):
    if not isinstance(persons, dict):
        return ""
    names = []
    for role in roles:
        names.extend(_clean_text(person.get("name", "")) for person in persons.get(role, []) if person.get("name"))
    return "; ".join(dict.fromkeys(name for name in names if name))


def _api_get(path, params=None):
    response = SESSION.get(
        f"{FINA_NINATEKA_API_URL}{path}",
        params={"platform": "BROWSER", **(params or {})},
        timeout=(8, REQUEST_TIMEOUT),
    )
    response.raise_for_status()
    return response.json()


def build_fina_video_list_url(first_result=0, max_results=FINA_PAGE_SIZE):
    return (
        f"{FINA_NINATEKA_API_URL}/products/vods?platform=BROWSER"
        f"&firstResult={int(first_result)}&maxResults={int(max_results)}&mainCategoryId[]={FINA_VIDEO_CATEGORY_ID}"
    )


def collect_fina_institutions():
    return [
        {
            "institution": FINA_INSTITUTION_NAME,
            "slug": slugify(FINA_INSTITUTION_NAME),
            "country": FINA_COUNTRY,
            "continent": country_to_continent(FINA_COUNTRY),
            "repository_code": FINA_REPOSITORY_CODE,
            "archive_type": FINA_ARCHIVE_TYPE,
            "fina_detail_url": FINA_HOME_URL,
            "external_url": FINA_VIDEO_LIST_URL,
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
        "repository_code": FINA_REPOSITORY_CODE,
        "archive_type": FINA_ARCHIVE_TYPE,
        "fina_detail_url": FINA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FINA_VIDEO_LIST_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_fina_record(item, detail=None, page_number=1):
    detail = detail or {}
    source = {**item, **detail}
    record_id = str(source.get("id") or "")
    categories = source.get("categories") or []
    tags = source.get("tags") or []
    countries = source.get("countries") or []
    persons = source.get("persons") or {}
    title = _clean_text(source.get("title"))
    category_names = _join_names(categories)
    tag_names = _join_names(tags)
    country_names = _join_names(countries)
    directors = _people_names(persons, ["DIRECTING"])
    production = _people_names(persons, ["PRODUCTION", "PRODUCER", "DISTRIBUTION"])
    year = _clean_text(source.get("productionYear") or source.get("year"))
    if not year:
        match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", " ".join([title, _clean_text(source.get("lead"))]))
        year = match.group(1) if match else ""
    access_flags = [
        "video=true" if source.get("video") is True else "",
        "payable=true" if source.get("payable") is True else "payable=false",
        "loginRequired=true" if source.get("loginRequired") is True else "loginRequired=false",
        "geoipManualLock=true" if source.get("geoipManualLock") is True else "",
        "downloadAvailable=true" if source.get("downloadAvailable") is True else "",
    ]
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro de vídeo materializado na API pública da Ninateka.",
                _clean_text(source.get("lead")),
                _clean_text(source.get("description")),
                f"categorias: {category_names}" if category_names else "",
                f"tags: {tag_names}" if tag_names else "",
                f"direção: {directors}" if directors else "",
                f"produção/distribuição: {production}" if production else "",
                f"países declarados: {country_names}" if country_names else "",
                f"duração: {source.get('duration')} segundos" if source.get("duration") else "",
                "; ".join(value for value in access_flags if value),
                f"thumbnail: {_first_image_url(source)}" if _first_image_url(source) else "",
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": record_id,
        "video_link": source.get("webUrl", ""),
        "page_url": source.get("webUrl", ""),
        "platform": FINA_PLATFORM_LABEL,
        "title": title,
        "subject": "; ".join(value for value in [category_names, tag_names, directors, country_names] if value),
        "description": description,
        "date": year or _clean_text(source.get("since")),
        "page_number": page_number,
        "duration": source.get("duration", ""),
        "payable": bool(source.get("payable")),
        "login_required": bool(source.get("loginRequired")),
        "browser_platform": any((entry.get("name") == "BROWSER") for entry in source.get("platforms", [])),
        "main_category_id": (source.get("mainCategory") or {}).get("id", ""),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": FINA_VIDEO_LIST_URL,
        "platform": record.get("platform", FINA_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record_id):
    try:
        return record_id, _api_get(f"/products/vods/{record_id}"), ""
    except Exception as error:
        return record_id, {}, str(error)


def collect_fina_dataset():
    institutions = collect_fina_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_id = {}
    page_by_id = {}
    total_count = 0

    first_result = 0
    page_number = 1
    while True:
        url = build_fina_video_list_url(first_result)
        try:
            payload = _api_get(
                "/products/vods",
                {
                    "firstResult": first_result,
                    "maxResults": FINA_PAGE_SIZE,
                    "mainCategoryId[]": FINA_VIDEO_CATEGORY_ID,
                },
            )
            meta = payload.get("meta") or {}
            total_count = int(meta.get("totalCount") or total_count or 0)
            items = payload.get("items") or []
            for item in items:
                if (item.get("mainCategory") or {}).get("id") != FINA_VIDEO_CATEGORY_ID:
                    continue
                if item.get("audio") is True and item.get("video") is not True:
                    continue
                record_id = str(item.get("id") or "")
                if record_id:
                    records_by_id.setdefault(record_id, item)
                    page_by_id.setdefault(record_id, page_number)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    "ok",
                    200,
                    len(items),
                    sum(1 for item in items if item.get("video") is True),
                    f"Página API {page_number}; Ninateka declarou {total_count} registros na categoria pública de vídeo.",
                )
            )
            first_result += FINA_PAGE_SIZE
            page_number += 1
            if not items or first_result >= total_count:
                break
            time.sleep(0.1)
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning="Falha na paginação da API Ninateka.", error=str(error)))
            break

    detail_by_id = {}
    with ThreadPoolExecutor(max_workers=FINA_DETAIL_WORKERS) as executor:
        futures = {executor.submit(_fetch_detail, record_id): record_id for record_id in records_by_id}
        for future in as_completed(futures):
            record_id, detail, error = future.result()
            detail_by_id[record_id] = detail
            web_url = detail.get("webUrl") or records_by_id.get(record_id, {}).get("webUrl") or f"{FINA_NINATEKA_URL}/"
            internal_pages.append(
                _internal_page_row(
                    institution,
                    web_url,
                    "erro" if error else "ok",
                    "" if error else 200,
                    0 if error else 1,
                    1 if detail.get("video") is True else 0,
                    "Ficha pública de vídeo Ninateka; usada para descrição, tags, créditos e regime de acesso.",
                    error,
                )
            )
            if error:
                errors.append(f"{record_id}: {error}")

    records = [
        parse_fina_record(item, detail_by_id.get(record_id), page_by_id.get(record_id, 1))
        for record_id, item in records_by_id.items()
    ]
    records = [record for record in records if record.get("video_link") and record.get("main_category_id") == FINA_VIDEO_CATEGORY_ID]
    video_links = [_record_to_video_row(institution, record) for record in records]
    public_count = sum(1 for record in records if not record.get("payable") and not record.get("login_required"))
    restricted_count = len(records) - public_count
    complete = bool(total_count) and len(records) == total_count
    summary = [
        {
            **_base_row(institution),
            "partner_site": FINA_VIDEO_LIST_URL,
            "partner_domain": normalize_domain(FINA_NINATEKA_URL),
            "status": "ok" if records else "sem_video_publico",
            "http_code": "200" if records else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": FINA_VIDEO_LIST_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": len(records) < FINA_MIN_VIDEO_TOTAL,
            "warning": (
                f"A API pública da Ninateka declarou {total_count} registros na categoria video e a rodada "
                f"materializou {len(records)} registros de vídeo, sem incorporar a categoria AUDIO. "
                f"Registros sem pagamento/cadastro detectado: {public_count}; registros com restrição declarada: {restricted_count}. "
                "O corpus representa a superfície pública Ninateka, não o acervo físico total da FINA."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "FINA_MIN_VIDEO_TOTAL",
    "collect_fina_dataset",
    "collect_fina_institutions",
    "parse_fina_record",
]
