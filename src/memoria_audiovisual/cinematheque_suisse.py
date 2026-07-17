import re
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

from .config import (
    CINEMATHEQUE_SUISSE_FILM_DEPARTMENT_URL,
    CINEMATHEQUE_SUISSE_HOME_URL,
    CINEMATHEQUE_SUISSE_MEMOBASE_INSTITUTION_URL,
    CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
    CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMATHEQUE_SUISSE_REPOSITORY_CODE = "CH-CINEMATHEQUE-SUISSE"
CINEMATHEQUE_SUISSE_ARCHIVE_TYPE = "National cinematheque with public metadata and onsite/authorized media access"
CINEMATHEQUE_SUISSE_COUNTRY = normalize_country("Switzerland")
CINEMATHEQUE_SUISSE_INSTITUTION_NAME = "Cinémathèque suisse"
CINEMATHEQUE_SUISSE_PLATFORM_LABEL = "Memobase LOD API"
CINEMATHEQUE_SUISSE_RECORDSET_CODE = "csa-001"
CINEMATHEQUE_SUISSE_SEARCH_QUERY = f"type:Film AND *:{CINEMATHEQUE_SUISSE_RECORDSET_CODE}"
CINEMATHEQUE_SUISSE_PAGE_SIZE = 40

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/ld+json, application/json, text/html;q=0.7",
        "Accept-Language": "fr-FR,fr;q=0.9,de;q=0.8,en;q=0.7,pt-BR;q=0.6",
    }
)


def _clean_text(value, *, limit=None):
    raw = str(value or "")
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True) if "<" in raw and ">" in raw else raw
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def _record_local_id(record_id):
    return str(record_id or "").replace("mbr:", "").strip()


def _record_api_url(record_id):
    local_id = _record_local_id(record_id)
    return f"https://api.memobase.ch/record/{local_id}?format=Json" if local_id else ""


def build_cinematheque_suisse_search_url(offset=0, size=CINEMATHEQUE_SUISSE_PAGE_SIZE):
    params = {
        "q": CINEMATHEQUE_SUISSE_SEARCH_QUERY,
        "format": "Json",
        "size": str(size),
        "offset": str(offset),
    }
    return f"{CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL}?{urlencode(params)}"


def fetch_memobase_json(url):
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    return response.json()


def _title(record):
    title = record.get("title")
    if isinstance(title, list):
        title = title[0] if title else ""
    if isinstance(title, dict):
        title = next((title.get(key) for key in ("@value", "title", "titleFr", "titleDe", "titleIt") if title.get(key)), "")
    if title:
        return _clean_text(title)
    for item in _as_list(record.get("hasOrHadTitle")):
        if isinstance(item, dict):
            value = next((item.get(key) for key in ("title", "titleFr", "titleDe", "titleIt") if item.get(key)), "")
            if value:
                return _clean_text(value)
    return _record_local_id(record.get("@id"))


def _first_date_value(value):
    for item in _as_list(value):
        if isinstance(item, dict):
            date_value = item.get("normalizedDateValue") or item.get("expressedDate")
            if date_value:
                return _clean_text(date_value)
        elif item:
            return _clean_text(item)
    return ""


def _record_date(record):
    return (
        _first_date_value(record.get("issued"))
        or _first_date_value(record.get("created"))
        or _first_date_value(record.get("temporal"))
    )


def _named_values(value, keys=("prefLabelFr", "prefLabelDe", "prefLabelIt", "prefLabel", "nameFr", "nameDe", "nameIt", "name"), limit=8):
    values = []
    for item in _as_list(value):
        if isinstance(item, dict):
            found = next((item.get(key) for key in keys if item.get(key)), "")
            if isinstance(found, list):
                found = found[0] if found else ""
            if found:
                cleaned = _clean_text(found)
                if cleaned and cleaned not in values:
                    values.append(cleaned)
        elif item:
            cleaned = _clean_text(item)
            if cleaned and cleaned not in values:
                values.append(cleaned)
        if len(values) >= limit:
            break
    return values


def _record_text(record, key, limit=1000):
    values = [_clean_text(value) for value in _as_list(record.get(key))]
    return _clean_text(" ".join(value for value in values if value), limit=limit)


def _rule_names(instantiation, rule_type):
    names = []
    for rule in _as_list(instantiation.get("isOrWasRegulatedBy")):
        if isinstance(rule, dict) and str(rule.get("type", "")).lower() == rule_type:
            name = _clean_text(rule.get("name"))
            if name and name not in names:
                names.append(name)
    return names


def _digital_access(record):
    fallback = {"locator": "", "media_location": "", "access": [], "usage": [], "thumbnail": ""}
    for instantiation in _as_list(record.get("hasInstantiation")):
        if not isinstance(instantiation, dict):
            continue
        instantiation_id = str(instantiation.get("@id", ""))
        instantiation_type = str(instantiation.get("type", ""))
        locator = _clean_text(instantiation.get("locator"))
        if instantiation_id.endswith("/derived") or instantiation_type == "thumbnail":
            if locator and not fallback["thumbnail"]:
                fallback["thumbnail"] = locator
            continue
        if instantiation_type == "digitalObject":
            return {
                "locator": locator,
                "media_location": _clean_text(instantiation.get("mediaLocation")),
                "access": _rule_names(instantiation, "access"),
                "usage": _rule_names(instantiation, "usage"),
                "thumbnail": fallback["thumbnail"],
            }
    return fallback


def collect_cinematheque_suisse_institutions():
    return [
        {
            "institution": CINEMATHEQUE_SUISSE_INSTITUTION_NAME,
            "slug": slugify(CINEMATHEQUE_SUISSE_INSTITUTION_NAME),
            "country": CINEMATHEQUE_SUISSE_COUNTRY,
            "continent": country_to_continent(CINEMATHEQUE_SUISSE_COUNTRY),
            "repository_code": CINEMATHEQUE_SUISSE_REPOSITORY_CODE,
            "archive_type": CINEMATHEQUE_SUISSE_ARCHIVE_TYPE,
            "cinematheque_suisse_detail_url": CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
            "external_url": CINEMATHEQUE_SUISSE_HOME_URL,
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
        "repository_code": CINEMATHEQUE_SUISSE_REPOSITORY_CODE,
        "archive_type": CINEMATHEQUE_SUISSE_ARCHIVE_TYPE,
        "cinematheque_suisse_detail_url": CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code=200, video_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": 0,
        "warning": warning,
        "error": error,
    }


def memobase_record_to_video_row(institution, record):
    access = _digital_access(record)
    record_id = _record_local_id(record.get("@id"))
    api_record_url = _record_api_url(record.get("@id"))
    genres = _named_values(record.get("hasGenre"), limit=4)
    subjects = _named_values(record.get("hasOrHadSubject"), limit=4)
    places = _named_values(record.get("hasPlaceOfCapture") or record.get("spatial"), limit=4)
    subject_parts = ["Film", "Collection film de la Cinémathèque suisse", *genres, *subjects, *places]
    access_label = ", ".join(access["access"]) or "regra de acesso não explicitada"
    usage_label = ", ".join(access["usage"]) or "uso não explicitado"
    description = _clean_text(
        " ".join(
            part
            for part in [
                _record_text(record, "abstract", limit=800),
                _record_text(record, "scopeAndContent", limit=500),
                f"Registro público via Memobase Linked Open Data API ({record_id}).",
                f"Mídia digital indicada por localizador técnico; acesso: {access_label}; uso: {usage_label}.",
                "A presença de localizador não equivale a vídeo público aberto; a própria rota informa acesso local/autorizado.",
            ]
            if part
        ),
        limit=1600,
    )
    return {
        **_base_row(institution),
        "partner_site": api_record_url or CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL,
        "platform": CINEMATHEQUE_SUISSE_PLATFORM_LABEL,
        "video_link": access["locator"] or api_record_url,
        "video_title": _title(record),
        "video_subject": _clean_text("; ".join(dict.fromkeys(part for part in subject_parts if part)), limit=700),
        "video_description": description,
        "video_published_at": _record_date(record),
    }


def collect_memobase_film_records(fetcher=fetch_memobase_json, page_size=CINEMATHEQUE_SUISSE_PAGE_SIZE):
    records = []
    seen = set()
    total = None
    offset = 0
    while total is None or offset < total:
        url = build_cinematheque_suisse_search_url(offset=offset, size=page_size)
        data = fetcher(url)
        members = data.get("hydra:member", [])
        total = int(data.get("hydra:totalItems", len(records) + len(members)) or 0)
        if not members:
            break
        for record in members:
            record_id = record.get("@id")
            if record_id in seen:
                continue
            seen.add(record_id)
            records.append(record)
        offset += len(members)
    return records, int(total or len(records))


def collect_cinematheque_suisse_dataset(fetcher=fetch_memobase_json):
    institutions = collect_cinematheque_suisse_institutions()
    institution = institutions[0]
    internal_pages = [
        _internal_page_row(
            institution,
            CINEMATHEQUE_SUISSE_FILM_DEPARTMENT_URL,
            "fonte_contextual_oficial",
            http_code="",
            warning="Página oficial do Departamento Film usada como evidência institucional; a coleta reprodutível usa a API Memobase.",
        )
    ]
    errors = []

    for url, label in [
        (CINEMATHEQUE_SUISSE_MEMOBASE_INSTITUTION_URL, "Instituição csa na API Memobase"),
        (CINEMATHEQUE_SUISSE_MEMOBASE_RECORDSET_URL, "Conjunto csa-001 na API Memobase"),
    ]:
        try:
            fetcher(url)
            internal_pages.append(_internal_page_row(institution, url, "ok", warning=label))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", http_code="", warning=label, error=str(error)))

    try:
        records, source_total = collect_memobase_film_records(fetcher=fetcher)
    except Exception as error:
        records, source_total = [], 0
        errors.append(f"{CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL}: {error}")

    search_url = build_cinematheque_suisse_search_url(offset=0)
    internal_pages.append(
        _internal_page_row(
            institution,
            search_url,
            "ok" if records else "sem_registros",
            video_count=len(records),
            warning=f"Consulta completa `type:Film AND *:{CINEMATHEQUE_SUISSE_RECORDSET_CODE}`; total informado pela API: {source_total}.",
            error=" | ".join(errors[:3]),
        )
    )

    video_links = [memobase_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL,
            "partner_domain": normalize_domain(CINEMATHEQUE_SUISSE_MEMOBASE_SEARCH_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records and len(records) == source_total else "parcial_ou_sem_registros",
            "final_url": search_url,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Protocolo de não incorporação: a unidade analítica é a Cinémathèque suisse, "
                "mas a rota reprodutível usa a API Linked Open Data do Memobase para o conjunto `csa-001`. "
                f"Foram coletados {len(records)} registros `Film` com metadados públicos; a mídia aparece como "
                "acesso local/autorizado, não como vídeo público incorporável ao corpus ativo."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMATHEQUE_SUISSE_ARCHIVE_TYPE",
    "CINEMATHEQUE_SUISSE_COUNTRY",
    "CINEMATHEQUE_SUISSE_INSTITUTION_NAME",
    "CINEMATHEQUE_SUISSE_PLATFORM_LABEL",
    "CINEMATHEQUE_SUISSE_RECORDSET_CODE",
    "CINEMATHEQUE_SUISSE_REPOSITORY_CODE",
    "build_cinematheque_suisse_search_url",
    "collect_cinematheque_suisse_dataset",
    "collect_cinematheque_suisse_institutions",
    "collect_memobase_film_records",
    "memobase_record_to_video_row",
]
