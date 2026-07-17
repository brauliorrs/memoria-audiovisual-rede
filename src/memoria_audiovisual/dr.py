from __future__ import annotations

import re
import time
from urllib.parse import urljoin

import requests

from .config import DR_API_BASE_URL, DR_DRTV_HOME_URL, DR_GENSYN_URL, DR_HOME_URL, HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


DR_REPOSITORY_CODE = "DK-DR"
DR_ARCHIVE_TYPE = "Public service broadcaster audiovisual archive with authenticated streaming"
DR_COUNTRY = normalize_country("Denmark")
DR_INSTITUTION_NAME = "DR - Danmarks Radio"
DR_PLATFORM_LABEL = "DRTV/Gensyn"
DR_LIST_PAGE_SIZE = 50
DR_MAX_SHOW_DETAIL_PAGES = 20
DR_REQUEST_PAUSE = 0.05

DR_GENSYN_PATHS = [
    "/gensyn",
    "/gensyn/historie",
    "/gensyn/kultur",
    "/gensyn/dokumentar",
    "/gensyn/teater-og-tv-film",
    "/gensyn/1950erne",
    "/gensyn/1960erne",
    "/gensyn/1970erne",
    "/gensyn/1980erne",
    "/gensyn/1990erne",
    "/gensyn/2000erne",
]

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept": "application/json,text/html,*/*", "Accept-Language": "da,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch_json(path, params=None):
    response = SESSION.get(urljoin(DR_API_BASE_URL + "/", path.lstrip("/")), params=params or {}, timeout=(8, REQUEST_TIMEOUT))
    response.raise_for_status()
    return response.json(), response.url, response.status_code


def _full_drtv_url(path):
    return urljoin(DR_DRTV_HOME_URL, str(path or "").lstrip("/"))


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


def _offer_values(item, field):
    return sorted({str(offer.get(field, "")).strip() for offer in item.get("offers") or [] if str(offer.get(field, "")).strip()})


def _is_open_stream(item):
    return any(offer.get("availability") == "Available" and offer.get("ownership") == "Free" for offer in item.get("offers") or [])


def _extract_list_ids(obj):
    ids = []

    def walk(value):
        if isinstance(value, dict):
            if str(value.get("id", "")).isdigit() and ("items" in value or "itemTypes" in value):
                ids.append(str(value["id"]))
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)
    return list(dict.fromkeys(ids))


def _extract_items(obj, item_types=("program", "episode", "show")):
    items = []

    def walk(value):
        if isinstance(value, dict):
            if value.get("type") in item_types and value.get("id"):
                items.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(obj)
    return items


def parse_dr_list_payload(payload):
    return [item for item in payload.get("items") or [] if item.get("type") in {"program", "episode", "show"} and item.get("id")]


def _record_id(item):
    return _clean_text(item.get("id") or item.get("customId"))


def _item_to_record(item, source_path="", collection_title=""):
    item_type = _clean_text(item.get("type"))
    custom_fields = item.get("customFields") or {}
    access_status = "aberto" if item_type in {"program", "episode"} and _is_open_stream(item) else "restrito_autenticado"
    page_path = item.get("path") or item.get("watchPath") or ""
    watch_path = item.get("watchPath") or page_path
    categories = [_clean_text(value) for value in item.get("categories") or [] if _clean_text(value)]
    keywords = [_clean_text(value) for value in item.get("keywords") or [] if _clean_text(value)]
    availability = ", ".join(_offer_values(item, "availability"))
    ownership = ", ".join(_offer_values(item, "ownership"))
    delivery = ", ".join(_offer_values(item, "deliveryType"))
    resolution = ", ".join(_offer_values(item, "resolution"))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                _clean_text(item.get("shortDescription")),
                f"tipo DRTV: {item_type}" if item_type else "",
                f"coleção: {collection_title}" if collection_title else "",
                f"categorias: {', '.join(categories)}" if categories else "",
                f"palavras-chave: {', '.join(keywords[:8])}" if keywords else "",
                f"ano: {item.get('releaseYear')}" if item.get("releaseYear") else "",
                f"duração: {_duration_text(item.get('duration'))}" if item.get("duration") else "",
                f"país de produção: {custom_fields.get('ProductionCountry')}" if custom_fields.get("ProductionCountry") else "",
                f"georrestrição declarada: {custom_fields.get('IsGeoRestricted')}" if custom_fields.get("IsGeoRestricted") else "",
                f"oferta DRTV: availability={availability or 'n/d'}; ownership={ownership or 'n/d'}; delivery={delivery or 'n/d'}; resolution={resolution or 'n/d'}",
                "regime de acesso: streaming com login/cadastro ou oferta não livre no nível do programa/episódio"
                if access_status == "restrito_autenticado"
                else "regime de acesso: oferta indicada como Available/Free no nível do programa/episódio",
                "ficha pública DRTV/Gensyn coletada por API pública; mídia não baixada",
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": _record_id(item),
        "title": _clean_text(custom_fields.get("PageTitle") or item.get("title")),
        "subject": "; ".join(value for value in [collection_title, *categories, *keywords[:5]] if value),
        "description": description,
        "date": _clean_text(custom_fields.get("AvailableFrom") or item.get("releaseYear")),
        "duration": _duration_text(item.get("duration")),
        "page_url": _full_drtv_url(page_path),
        "watch_url": _full_drtv_url(watch_path),
        "source_path": source_path,
        "item_type": item_type,
        "access_status": access_status,
        "availability": availability,
        "ownership": ownership,
    }


def collect_dr_institutions():
    return [
        {
            "institution": DR_INSTITUTION_NAME,
            "slug": slugify("dr-danmarks-radio"),
            "country": DR_COUNTRY,
            "continent": country_to_continent(DR_COUNTRY),
            "repository_code": DR_REPOSITORY_CODE,
            "archive_type": DR_ARCHIVE_TYPE,
            "dr_detail_url": DR_GENSYN_URL,
            "external_url": DR_HOME_URL,
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
        "repository_code": DR_REPOSITORY_CODE,
        "archive_type": DR_ARCHIVE_TYPE,
        "dr_detail_url": DR_GENSYN_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": DR_GENSYN_URL,
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
        "partner_site": DR_GENSYN_URL,
        "platform": DR_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_dr_dataset():
    institutions = collect_dr_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    show_paths = []
    errors = []
    list_ids = {}

    for path in DR_GENSYN_PATHS:
        try:
            payload, url, status = _fetch_json("/page", {"path": path})
            page_title = _clean_text(payload.get("title"))
            page_list_ids = _extract_list_ids(payload)
            for list_id in page_list_ids:
                list_ids.setdefault(list_id, page_title or path)
            internal_pages.append(
                _internal_page_row(institution, url, "ok", status, warning=f"Página pública DRTV/Gensyn `{path}`; listas detectadas: {len(page_list_ids)}.")
            )
        except Exception as error:
            errors.append(f"{path}: {error}")
            internal_pages.append(_internal_page_row(institution, _full_drtv_url(path), "erro", warning="Falha ao consultar página DRTV/Gensyn.", error=str(error)))

    for list_id, collection_title in list_ids.items():
        page = 1
        total_pages = 1
        while page <= total_pages:
            try:
                payload, url, status = _fetch_json(f"/lists/{list_id}", {"page_size": DR_LIST_PAGE_SIZE, "page": page})
                total_pages = int((payload.get("paging") or {}).get("total") or 1)
                page_items = parse_dr_list_payload(payload)
                for item in page_items:
                    if item.get("type") == "show" and item.get("path"):
                        show_paths.append(item["path"])
                    if item.get("type") in {"program", "episode"}:
                        record = _item_to_record(item, collection_title=collection_title)
                        records_by_id.setdefault(record["record_id"], record)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        url,
                        "ok",
                        status,
                        sum(1 for item in page_items if item.get("type") in {"program", "episode"}),
                        0,
                        f"Lista DRTV/Gensyn {list_id}, página {page}/{total_pages}; coleção: {collection_title}.",
                    )
                )
            except Exception as error:
                errors.append(f"lista {list_id} página {page}: {error}")
                internal_pages.append(_internal_page_row(institution, f"{DR_API_BASE_URL}/lists/{list_id}", "erro", warning="Falha ao consultar lista DRTV/Gensyn.", error=str(error)))
                break
            page += 1
            time.sleep(DR_REQUEST_PAUSE)

    for show_path in list(dict.fromkeys(show_paths))[:DR_MAX_SHOW_DETAIL_PAGES]:
        try:
            payload, url, status = _fetch_json("/page", {"path": show_path})
            detail_items = _extract_items(payload, ("episode", "program"))
            for item in detail_items:
                record = _item_to_record(item, source_path=show_path, collection_title=_clean_text(payload.get("title")))
                records_by_id.setdefault(record["record_id"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    "ok",
                    status,
                    len(detail_items),
                    0,
                    f"Página de série DRTV/Gensyn `{show_path}` sondada para materializar episódios.",
                )
            )
        except Exception as error:
            errors.append(f"série {show_path}: {error}")
            internal_pages.append(_internal_page_row(institution, _full_drtv_url(show_path), "erro", warning="Falha ao sondar série DRTV/Gensyn.", error=str(error)))
        time.sleep(DR_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("page_url")]
    restricted_total = sum(1 for record in records if record.get("access_status") == "restrito_autenticado")
    open_total = len(records) - restricted_total
    summary = [
        {
            **_base_row(institution),
            "partner_site": DR_GENSYN_URL,
            "partner_domain": normalize_domain(DR_GENSYN_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": DR_GENSYN_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": open_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if video_links else "alta",
            "warning": (
                "Corpus DR incorporado pela rota pública DRTV/Gensyn. O MVP materializa páginas públicas "
                f"de programas/episódios a partir de {len(list_ids)} listas e {min(len(set(show_paths)), DR_MAX_SHOW_DETAIL_PAGES)} séries. "
                f"Registros com oferta não livre ou login/cadastro: {restricted_total}; registros com oferta Available/Free no nível do vídeo: {open_total}. "
                "Não baixa mídia, não representa o DR-arkivet integral da Biblioteca Real e não mistura materiais sem imagem em movimento."
            ),
            "error": "; ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "DR_ARCHIVE_TYPE",
    "DR_INSTITUTION_NAME",
    "DR_PLATFORM_LABEL",
    "DR_REPOSITORY_CODE",
    "collect_dr_dataset",
    "collect_dr_institutions",
    "parse_dr_list_payload",
]
