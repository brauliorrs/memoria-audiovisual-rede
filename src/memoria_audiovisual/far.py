from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    FAR_API_URL,
    FAR_FILMS_URL,
    FAR_HOME_URL,
    FAR_MFNA_HOME_URL,
    FAR_VIDEO_BASE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FAR_INSTITUTION_NAME = "Fonds Audiovisuel de Recherche"
FAR_REPOSITORY_CODE = "FR-FAR"
FAR_ARCHIVE_TYPE = "Local audiovisual archive with public film catalog"
FAR_COUNTRY = normalize_country("France")
FAR_PLATFORM_LABEL = "MFNA / FAR"
FAR_LIBRARY_ID = 2
FAR_PAGE_SIZE = 500
FAR_DETAIL_WORKERS = 6
FAR_MIN_VIDEO_TOTAL = 400
FAR_FILTER_KEYS = {"changeGenre": "genre", "changeTheme": "theme", "changeFormat": "format"}
FAR_AUDIO_ONLY_MARKERS = ("journal radio", "archives sonores", "bande son")
FAR_AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac")

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7",
        "Referer": FAR_FILMS_URL,
        "X-Requested-With": "XMLHttpRequest",
    }
)


def _clean_text(value, *, limit=None):
    raw = html.unescape(str(value or ""))
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True) if "<" in raw else raw
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _normalized(value):
    text = unicodedata.normalize("NFKD", _clean_text(value).lower())
    return "".join(char for char in text if not unicodedata.combining(char))


def _label(code, labels, field):
    if code in (None, ""):
        return ""
    return labels.get(field, {}).get(str(code), str(code))


def _labels_from_films_page(html_text):
    labels = {"genre": {}, "theme": {}, "format": {}}
    soup = BeautifulSoup(html_text or "", "html.parser")
    for select in soup.find_all("select", attrs={"data-action": True}):
        field = FAR_FILTER_KEYS.get(select.get("data-action"))
        if not field or labels[field]:
            continue
        for option in select.find_all("option"):
            value = _clean_text(option.get("value"))
            label = _clean_text(option.get_text(" ", strip=True))
            if value and label and not _normalized(label).startswith(("tout ", "toute ")):
                labels[field][str(value)] = label
    return labels


def _join_people(values):
    if not isinstance(values, list):
        return ""
    names = []
    for item in values:
        if not isinstance(item, dict):
            continue
        name = _clean_text(item.get("raison") or " ".join(part for part in [item.get("prenom"), item.get("nom")] if part))
        if name:
            names.append(name)
    return "; ".join(dict.fromkeys(names))


def _theme_labels(record, labels):
    codes = [record.get("theme")]
    codes.extend(code.strip() for code in str(record.get("themes_secondaires") or "").split(",") if code.strip())
    return "; ".join(dict.fromkeys(_label(code, labels, "theme") for code in codes if _label(code, labels, "theme")))


def build_far_search_payload(page=1, results_per_page=FAR_PAGE_SIZE):
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
            "general": {"sid": FAR_LIBRARY_ID, "genre": None, "theme": None, "dossier": None},
        },
    }


def build_far_film_page_url(record):
    slug = record.get("slug") or ""
    if not slug and record.get("internet_permalien"):
        slug = f"films/{record['internet_permalien']}"
    return urljoin(FAR_MFNA_HOME_URL, slug.lstrip("/")) if slug else FAR_FILMS_URL


def build_far_video_url(record):
    if record.get("video_url"):
        return str(record["video_url"])
    if record.get("enveloppe") and record.get("film"):
        filename = quote(str(record["film"]), safe="-_.~()+")
        return f"{FAR_VIDEO_BASE_URL.rstrip('/')}/{record['enveloppe']}/{filename}"
    return ""


def is_audio_only_far_record(record, labels=None):
    labels = labels or {"genre": {}, "theme": {}, "format": {}}
    values = [
        _label(record.get("genre"), labels, "genre"),
        _theme_labels(record, labels),
        _label(record.get("format_original"), labels, "format"),
    ]
    if any(marker in _normalized(value) for value in values for marker in FAR_AUDIO_ONLY_MARKERS):
        return True
    media_url = _normalized(record.get("video_url") or record.get("film") or "")
    return media_url.endswith(FAR_AUDIO_EXTENSIONS)


def parse_far_record(record, labels=None, page_number=1):
    labels = labels or {"genre": {}, "theme": {}, "format": {}}
    genre = _label(record.get("genre"), labels, "genre")
    themes = _theme_labels(record, labels)
    original_format = _label(record.get("format_original"), labels, "format")
    directors = _join_people(record.get("realisateurs_decoded"))
    page_url = build_far_film_page_url(record)
    video_url = build_far_video_url(record)
    audio_only = is_audio_only_far_record(record, labels)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro de filme materializado no catálogo público MFNA/FAR.",
                _clean_text(record.get("resume")),
                _clean_text(record.get("descriptif")),
                f"gênero: {genre}" if genre else "",
                f"temas: {themes}" if themes else "",
                f"formato original: {original_format}" if original_format else "",
                f"duração: {record.get('duree')}" if record.get("duree") else "",
                f"realização: {directors}" if directors else "",
                f"ficha pública: {page_url}",
                f"miniatura: {record.get('image_chemin')}" if record.get("image_chemin") else "",
                "excluído por ausência de imagem em movimento" if audio_only else "",
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": str(record.get("id") or f"{record.get('sid', '')}-{record.get('oid', '')}"),
        "video_link": video_url,
        "page_url": page_url,
        "platform": FAR_PLATFORM_LABEL,
        "title": _clean_text(record.get("titre")),
        "subject": "; ".join(value for value in [genre, themes, directors] if value),
        "description": description,
        "date": _clean_text(record.get("annee") or record.get("periode_debut") or record.get("date")),
        "page_number": page_number,
        "duration": _clean_text(record.get("duree")),
        "audio_only": audio_only,
        "genre": genre,
        "themes": themes,
        "format_original": original_format,
        "internet_visible": record.get("internet_visible"),
    }


def collect_far_institutions():
    return [
        {
            "institution": FAR_INSTITUTION_NAME,
            "slug": slugify(FAR_INSTITUTION_NAME),
            "country": FAR_COUNTRY,
            "continent": country_to_continent(FAR_COUNTRY),
            "repository_code": FAR_REPOSITORY_CODE,
            "archive_type": FAR_ARCHIVE_TYPE,
            "far_detail_url": FAR_HOME_URL,
            "external_url": FAR_FILMS_URL,
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
        "repository_code": FAR_REPOSITORY_CODE,
        "archive_type": FAR_ARCHIVE_TYPE,
        "far_detail_url": FAR_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FAR_FILMS_URL,
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
        "partner_site": FAR_FILMS_URL,
        "platform": record.get("platform", FAR_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _post_action(action, **data):
    response = SESSION.post(
        FAR_API_URL,
        data={"action": action, **data},
        timeout=(8, REQUEST_TIMEOUT),
    )
    response.raise_for_status()
    return response.json()


def _extract_total_count(payload, fallback=0):
    count = payload.get("count")
    if isinstance(count, dict):
        count = count.get("nbr")
    try:
        return int(count)
    except (TypeError, ValueError):
        return fallback


def _fetch_detail(item):
    key = (item.get("sid"), item.get("oid"))
    try:
        return key, _post_action("back.film.getFilm", sid=str(item.get("sid")), oid=str(item.get("oid"))), ""
    except Exception as error:
        return key, item, str(error)


def collect_far_dataset():
    institutions = collect_far_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    labels = {"genre": {}, "theme": {}, "format": {}}
    raw_records = {}
    page_by_key = {}
    total_count = 0

    try:
        response = SESSION.get(FAR_FILMS_URL, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        response.raise_for_status()
        labels = _labels_from_films_page(response.text)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                0,
                0,
                "Interface pública de filmes MFNA/FAR; usada para confirmar filtros de gênero, tema e formato.",
            )
        )
    except Exception as error:
        errors.append(f"{FAR_FILMS_URL}: {error}")
        internal_pages.append(_internal_page_row(institution, FAR_FILMS_URL, "erro", warning="Falha ao abrir a interface pública de filmes.", error=str(error)))

    page = 1
    while True:
        payload = build_far_search_payload(page=page)
        try:
            data = _post_action("back.film.getFilms", data=json.dumps(payload, separators=(",", ":")))
            items = data.get("data") or []
            total_count = _extract_total_count(data, total_count)
            for item in items:
                key = (item.get("sid"), item.get("oid"))
                raw_records.setdefault(key, item)
                page_by_key.setdefault(key, page)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{FAR_API_URL}?action=back.film.getFilms&page={page}&sid={FAR_LIBRARY_ID}",
                    "ok",
                    200,
                    len(items),
                    len(items),
                    f"Página API {page}; a rota MFNA/FAR declarou {total_count or len(raw_records)} registros para o FAR.",
                )
            )
            if not items or (total_count and len(raw_records) >= total_count):
                break
            page += 1
            time.sleep(0.1)
        except Exception as error:
            errors.append(f"film.getFilms page {page}: {error}")
            internal_pages.append(_internal_page_row(institution, FAR_API_URL, "erro", warning="Falha na paginação da API MFNA/FAR.", error=str(error)))
            break

    detail_by_key = {}
    with ThreadPoolExecutor(max_workers=FAR_DETAIL_WORKERS) as executor:
        futures = {executor.submit(_fetch_detail, item): key for key, item in raw_records.items()}
        for future in as_completed(futures):
            key, detail, error = future.result()
            detail_by_key[key] = detail
            record = parse_far_record({**raw_records.get(key, {}), **detail}, labels, page_by_key.get(key, 1))
            internal_pages.append(
                _internal_page_row(
                    institution,
                    record.get("page_url") or FAR_FILMS_URL,
                    "erro" if error else "ok",
                    "" if error else 200,
                    0 if error or record.get("audio_only") else int(bool(record.get("video_link"))),
                    0 if error or record.get("audio_only") else int(bool(record.get("video_link"))),
                    "Ficha pública de filme MFNA/FAR com metadados e URL de vídeo MP4, sem baixar mídia.",
                    error,
                )
            )
            if error:
                errors.append(f"{key}: {error}")

    records = []
    audio_excluded = 0
    seen_links = set()
    for key, item in raw_records.items():
        record = parse_far_record({**item, **detail_by_key.get(key, {})}, labels, page_by_key.get(key, 1))
        if record.get("audio_only"):
            audio_excluded += 1
            continue
        video_link = record.get("video_link")
        if not video_link or video_link in seen_links:
            continue
        seen_links.add(video_link)
        records.append(record)

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete = bool(total_count) and len(raw_records) == total_count
    summary = [
        {
            **_base_row(institution),
            "partner_site": FAR_FILMS_URL,
            "partner_domain": normalize_domain(FAR_MFNA_HOME_URL),
            "status": "ok" if records else "sem_video_publico",
            "http_code": "200" if records else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": FAR_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": len(video_links) < FAR_MIN_VIDEO_TOTAL or not complete,
            "warning": (
                f"A rota pública MFNA/FAR declarou {total_count or len(raw_records)} registros para o FAR "
                f"(sid={FAR_LIBRARY_ID}); a rodada coletou {len(raw_records)} registros, incorporou {len(video_links)} "
                f"filmes com URL MP4 pública e excluiu {audio_excluded} registro(s) sem imagem em movimento por regra de escopo. "
                "O corpus representa a superfície pública enumerável do FAR, não o acervo físico, interno ou não publicado."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "FAR_MIN_VIDEO_TOTAL",
    "build_far_film_page_url",
    "build_far_search_payload",
    "build_far_video_url",
    "collect_far_dataset",
    "collect_far_institutions",
    "is_audio_only_far_record",
    "parse_far_record",
]
