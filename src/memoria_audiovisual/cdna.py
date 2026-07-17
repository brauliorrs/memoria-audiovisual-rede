import html
import json
import re
import time
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CDNA_API_URL,
    CDNA_FILMS_URL,
    CDNA_HOME_URL,
    CDNA_VIDEO_BASE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CDNA_REPOSITORY_CODE = "FR-CDNA"
CDNA_ARCHIVE_TYPE = "Regional audiovisual and amateur film archive"
CDNA_COUNTRY = normalize_country("France")
CDNA_INSTITUTION_NAME = "Cinémathèque de Nouvelle-Aquitaine"
CDNA_PLATFORM_LABEL = "Cinémathèque de Nouvelle-Aquitaine"
CDNA_MAX_API_PAGES = 3
CDNA_RESULTS_PER_PAGE = 24


def _new_session():
    session = requests.Session()
    session.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})
    return session


def _clean_text(value, *, limit=None):
    text = BeautifulSoup(html.unescape(str(value or "")), "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _search_payload(page=1, results_per_page=CDNA_RESULTS_PER_PAGE):
    return {
        "currentPage": int(page),
        "resultsPerPage": int(results_per_page),
        "orderBy": "date",
        "sort": "DESC",
        "filters": {
            "globalSearch": None,
            "duration": None,
            "periode_debut": "",
            "periode_fin": "",
            "annee": "",
            "format": None,
            "colorisation": "all",
            "realisateur": "",
            "deposant": "",
            "general": {"sid": 1, "genre": None, "theme": None, "dossier": None},
        },
    }


def fetch_cdna_catalog_page(session, page=1, results_per_page=CDNA_RESULTS_PER_PAGE):
    session.get(CDNA_FILMS_URL, timeout=(8, REQUEST_TIMEOUT))
    response = session.post(
        CDNA_API_URL,
        data={
            "action": "back.film.getFilms",
            "data": json.dumps(_search_payload(page, results_per_page), ensure_ascii=False),
        },
        headers={"Referer": CDNA_FILMS_URL, "X-Requested-With": "XMLHttpRequest"},
        timeout=(8, REQUEST_TIMEOUT),
    )
    response.raise_for_status()
    return response


def collect_cdna_institutions():
    return [
        {
            "institution": CDNA_INSTITUTION_NAME,
            "slug": slugify(CDNA_INSTITUTION_NAME),
            "country": CDNA_COUNTRY,
            "continent": country_to_continent(CDNA_COUNTRY),
            "repository_code": CDNA_REPOSITORY_CODE,
            "archive_type": CDNA_ARCHIVE_TYPE,
            "cdna_detail_url": CDNA_HOME_URL,
            "external_url": CDNA_FILMS_URL,
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
        "repository_code": CDNA_REPOSITORY_CODE,
        "archive_type": CDNA_ARCHIVE_TYPE,
        "cdna_detail_url": CDNA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CDNA_FILMS_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def _detail_url(row):
    return urljoin(CDNA_HOME_URL, str(row.get("slug") or f"films/{row.get('internet_permalien', '')}"))


def _video_url(row):
    if row.get("youtube"):
        return str(row["youtube"])
    if row.get("enveloppe") and row.get("film"):
        return f"{CDNA_VIDEO_BASE_URL}/{quote(str(row['enveloppe']))}/{quote(str(row['film']))}"
    return _detail_url(row)


def _people_names(row, key="realisateurs_decoded"):
    names = []
    for person in row.get(key) or []:
        if person.get("mention") == "3" and person.get("mention_nom"):
            names.append(_clean_text(person.get("mention_nom")))
        elif str(person.get("type")) == "2":
            names.append(_clean_text(f"{person.get('prenom', '')} {person.get('nom', '')}"))
        elif person.get("raison"):
            names.append(_clean_text(person.get("raison")))
    return [name for name in names if name]


def _record_id(row):
    return str(row.get("oid") or row.get("id") or row.get("supportId") or "")


def _record_to_catalog_record(row):
    creators = _people_names(row)
    detail_url = _detail_url(row)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública da CdNA; registro materializado a partir do endpoint público de filmes.",
                f"duração: {row.get('duree')}" if row.get("duree") else "",
                f"ano/período: {row.get('annee')}" if row.get("annee") else "",
                f"realização: {', '.join(creators)}" if creators else "",
                f"data de publicação: {row.get('date_publication')}" if row.get("date_publication") else "",
                _clean_text(row.get("resume"), limit=700),
                _clean_text(row.get("descriptif"), limit=1200),
            ]
            if value
        ),
        limit=2200,
    )
    return {
        "record_id": _record_id(row),
        "source_kind": "cdna_public_api_record",
        "page_url": detail_url,
        "video_link": _video_url(row),
        "platform": CDNA_PLATFORM_LABEL,
        "title": _clean_text(row.get("titre"), limit=250),
        "subject": "; ".join(creators),
        "description": description,
        "date": _clean_text(row.get("annee") or row.get("periode_debut") or row.get("date_publication")),
        "embedded": bool(row.get("film") or row.get("youtube")),
    }


def parse_cdna_api_payload(payload):
    records = [_record_to_catalog_record(row) for row in payload.get("data") or []]
    declared_total = int((payload.get("count") or {}).get("nbr") or len(records))
    return records, declared_total


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CDNA_FILMS_URL,
        "platform": CDNA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_cdna_dataset():
    institutions = collect_cdna_institutions()
    institution = institutions[0]
    session = _new_session()
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_total = 0

    for url, warning in [
        (CDNA_HOME_URL, "Site institucional da Cinémathèque de Nouvelle-Aquitaine."),
        (CDNA_FILMS_URL, "Rota pública `Films`; rota principal de coleta via endpoint Onemo."),
    ]:
        try:
            response = session.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CDNA_MAX_API_PAGES + 1):
        try:
            response = fetch_cdna_catalog_page(session, page=page)
            page_records, total = parse_cdna_api_payload(response.json())
            declared_total = max(declared_total, total)
            for record in page_records:
                if record["record_id"]:
                    records_by_id[record["record_id"]] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{CDNA_API_URL}?action=back.film.getFilms&page={page}",
                    "ok",
                    response.status_code,
                    len(page_records),
                    sum(1 for record in page_records if record.get("embedded")),
                    f"Página {page} do endpoint público Onemo `back.film.getFilms`.",
                )
            )
            if len(page_records) < CDNA_RESULTS_PER_PAGE:
                break
            time.sleep(0.2)
        except Exception as error:
            errors.append(f"api_page_{page}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{CDNA_API_URL}?action=back.film.getFilms&page={page}",
                    "erro",
                    warning="Falha ao consultar endpoint público de filmes da CdNA.",
                    error=str(error),
                )
            )

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": CDNA_FILMS_URL,
            "partner_domain": normalize_domain(CDNA_FILMS_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CDNA_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo endpoint público `back.film.getFilms` da plataforma "
                "Mémoire Filmique de Nouvelle-Aquitaine. O endpoint declarou "
                f"{declared_total or 'múltiplos'} filmes para a CdNA; o MVP materializa "
                f"{len(records)} registros em até {CDNA_MAX_API_PAGES} páginas públicas, sem baixar mídia "
                "e sem afirmar cobertura total do acervo preservado."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CDNA_ARCHIVE_TYPE",
    "CDNA_COUNTRY",
    "CDNA_INSTITUTION_NAME",
    "CDNA_MAX_API_PAGES",
    "CDNA_PLATFORM_LABEL",
    "CDNA_REPOSITORY_CODE",
    "CDNA_RESULTS_PER_PAGE",
    "collect_cdna_dataset",
    "collect_cdna_institutions",
    "fetch_cdna_catalog_page",
    "parse_cdna_api_payload",
]
