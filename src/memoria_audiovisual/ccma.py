import re
import time
from datetime import datetime
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .config import (
    CCMA_ARCHIVE_SALES_URL,
    CCMA_CORPORATE_URL,
    CCMA_HOME_URL,
    CCMA_SEARCH_API_URL,
    CCMA_VIDEO_API_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CCMA_REPOSITORY_CODE = "ES-CCMA"
CCMA_ARCHIVE_TYPE = "Public service broadcaster digital video archive"
CCMA_COUNTRY = normalize_country("Spain")
CCMA_INSTITUTION_NAME = "Corporació Catalana de Mitjans Audiovisuals (CCMA) / 3Cat"
CCMA_PLATFORM_LABEL = "3Cat"
CCMA_SEARCH_TEXT = "Descobreix l'arxiu de TV3"
CCMA_MAX_SEARCH_PAGES = 2
CCMA_ITEMS_PER_PAGE = 12
CCMA_REQUEST_PAUSE = 0.15

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "ca,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _strip_html(value):
    return _clean_text(BeautifulSoup(str(value or ""), "html.parser").get_text(" ", strip=True))


def _format_ccma_date(value):
    text = _clean_text(value)
    for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return text


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _request_json(url, params):
    response = _fetch(url, params=params, headers={"Accept": "application/json", **SESSION.headers})
    response.raise_for_status()
    return response.url, response.json()


def collect_ccma_institutions():
    return [
        {
            "institution": CCMA_INSTITUTION_NAME,
            "slug": slugify("ccma-3cat"),
            "country": CCMA_COUNTRY,
            "continent": country_to_continent(CCMA_COUNTRY),
            "repository_code": CCMA_REPOSITORY_CODE,
            "archive_type": CCMA_ARCHIVE_TYPE,
            "ccma_detail_url": CCMA_HOME_URL,
            "external_url": CCMA_HOME_URL,
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
        "repository_code": CCMA_REPOSITORY_CODE,
        "archive_type": CCMA_ARCHIVE_TYPE,
        "ccma_detail_url": CCMA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CCMA_HOME_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def build_ccma_search_url(page=1):
    return f"{CCMA_SEARCH_API_URL}?{urlencode(_search_params(page))}"


def _search_params(page=1):
    return {
        "_format": "json",
        "text": CCMA_SEARCH_TEXT,
        "tipologia": "DTY_VIDEO_MM",
        "items_pagina": CCMA_ITEMS_PER_PAGE,
        "pagina": int(page),
        "sdom": "img",
        "version": "2.0",
        "cache": "180",
        "https": "true",
        "master": "yes",
    }


def _video_params(video_id):
    return {
        "_format": "json",
        "id": str(video_id),
        "no_agrupacio": "PUAG_PROGVID",
        "origen": "item",
        "pagina": 1,
        "sdom": "img",
        "version": "2.0",
        "cache": "180",
        "https": "true",
        "master": "yes",
    }


def parse_ccma_search_payload(payload):
    resposta = (payload or {}).get("resposta", {})
    items = resposta.get("items", {})
    raw_items = items.get("item", []) if isinstance(items, dict) else items if isinstance(items, list) else []
    records = []
    for item in raw_items:
        video_id = str(item.get("id") or "").strip()
        if video_id and item.get("tipologia") == "DTY_VIDEO_MM":
            records.append({"record_id": video_id, "title": _clean_text(item.get("titol")), "raw": item})
    return records


def _values(items, key="desc"):
    if not isinstance(items, list):
        return []
    return [_clean_text(item.get(key)) for item in items if _clean_text(item.get(key))]


def _image_url(item):
    images = item.get("imatges") if isinstance(item, dict) else []
    if not isinstance(images, list) or not images:
        return ""
    preferred = sorted(images, key=lambda image: len(str(image.get("text", ""))), reverse=True)
    return _clean_text(preferred[0].get("text"))


def _canonical_url(item):
    video_id = item.get("id")
    slug = _clean_text(item.get("nom_friendly"))
    if slug:
        return f"https://www.3cat.cat/3cat/{slug}/video/{video_id}/"
    return f"https://www.3cat.cat/3cat/video/{video_id}/"


def _embed_url(video_id):
    return f"https://www.3cat.cat/3cat/video/{video_id}/embed/?tipus_embed=google"


def parse_ccma_video_item(item):
    video_id = str(item.get("id") or "").strip()
    canonical_url = _canonical_url(item)
    embed_url = _embed_url(video_id)
    title = _clean_text(item.get("titol") or item.get("permatitle"))
    teaser = _strip_html(item.get("entradeta"))
    program = _clean_text(item.get("programa") or item.get("permatitle"))
    archive_series = _clean_text(item.get("avantitol"))
    subject_parts = [
        archive_series,
        program,
        item.get("tipus_contingut"),
        item.get("tipologia"),
        *(_values(item.get("bbands"))),
        *(_values(item.get("idiomes"))),
        *(_values(item.get("geolocalitzacions"))),
    ]
    image_url = _image_url(item)
    video_date = _format_ccma_date(item.get("data_emissio") or item.get("data_publicacio") or item.get("data_creacio") or "")
    description = _clean_text(
        " | ".join(
            value
            for value in [
                teaser,
                f"recorte: {CCMA_SEARCH_TEXT}",
                f"duração: {item.get('durada')}" if item.get("durada") else "",
                f"emissão: {item.get('data_emissio')}" if item.get("data_emissio") else "",
                f"publicação: {item.get('data_publicacio')}" if item.get("data_publicacio") else "",
                "player público 3Cat registrado sem baixar mídia",
                f"embed: {embed_url}",
                f"imagem: {image_url}" if image_url else "",
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": video_id,
        "source_kind": "ccma_3cat_video_api",
        "video_link": embed_url if item.get("embedable") else canonical_url,
        "page_url": canonical_url,
        "platform": CCMA_PLATFORM_LABEL,
        "title": title,
        "subject": "; ".join(_clean_text(value) for value in subject_parts if _clean_text(value)),
        "description": description,
        "date": video_date,
        "video_title": title,
        "video_subject": "; ".join(_clean_text(value) for value in subject_parts if _clean_text(value)),
        "video_description": description,
        "video_published_at": video_date,
        "embedded": bool(item.get("embedable")),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": record.get("page_url") or CCMA_HOME_URL,
        "platform": CCMA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_ccma_dataset():
    institutions = collect_ccma_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []

    for url, warning in [
        (CCMA_HOME_URL, "Plataforma pública 3Cat, acesso sob demanda a vídeos."),
        (CCMA_CORPORATE_URL, "Página corporativa que identifica a CCMA/3Cat como grupo audiovisual público."),
        (CCMA_ARCHIVE_SALES_URL, "Serviço de venda/cópia de imagens de arquivo; documentado como acesso sob demanda, fora do corpus público coletado."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CCMA_MAX_SEARCH_PAGES + 1):
        try:
            search_url, payload = _request_json(CCMA_SEARCH_API_URL, _search_params(page))
            listed_records = parse_ccma_search_payload(payload)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    search_url,
                    "ok",
                    200,
                    len(listed_records),
                    0,
                    f"Página {page} da busca pública 3Cat por `{CCMA_SEARCH_TEXT}`.",
                )
            )
        except Exception as error:
            errors.append(f"{CCMA_SEARCH_API_URL}: {error}")
            internal_pages.append(_internal_page_row(institution, build_ccma_search_url(page), "erro", warning="Falha ao consultar busca pública 3Cat.", error=str(error)))
            continue

        for listed_record in listed_records:
            record_id = listed_record["record_id"]
            if record_id in records_by_id:
                continue
            try:
                video_url, detail_payload = _request_json(CCMA_VIDEO_API_URL, _video_params(record_id))
                item = detail_payload.get("resposta", {}).get("item", {})
                parsed = parse_ccma_video_item(item)
                records_by_id[record_id] = {**listed_record, **parsed}
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        video_url,
                        "ok",
                        200,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha JSON pública 3Cat verificada, com página/player registrado sem baixar mídia.",
                    )
                )
            except Exception as error:
                errors.append(f"{record_id}: {error}")
                internal_pages.append(_internal_page_row(institution, f"{CCMA_VIDEO_API_URL}?id={record_id}", "erro", warning="Falha ao abrir ficha JSON pública 3Cat.", error=str(error)))
            time.sleep(CCMA_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("video_link")]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CCMA_HOME_URL,
            "partner_domain": normalize_domain(CCMA_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": build_ccma_search_url(1),
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": (
                f"Recorte MVP: busca pública 3Cat por `{CCMA_SEARCH_TEXT}`, restrita a `DTY_VIDEO_MM`, "
                f"até {CCMA_MAX_SEARCH_PAGES} páginas. Não é o acervo integral da CCMA; o serviço de venda "
                "de imagens de arquivo é registrado como superfície restrita/sob demanda, fora do corpus público."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CCMA_ARCHIVE_TYPE",
    "CCMA_COUNTRY",
    "CCMA_INSTITUTION_NAME",
    "CCMA_PLATFORM_LABEL",
    "CCMA_REPOSITORY_CODE",
    "build_ccma_search_url",
    "collect_ccma_dataset",
    "collect_ccma_institutions",
    "parse_ccma_search_payload",
    "parse_ccma_video_item",
]
