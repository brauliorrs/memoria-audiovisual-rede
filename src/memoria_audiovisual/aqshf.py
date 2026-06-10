import html
import re
import time

import requests
from bs4 import BeautifulSoup

from .config import (
    AQSHF_HOME_URL,
    AQSHF_MOTION_PICTURES_URL,
    AQSHF_STATISTICS_URL,
    AQSHF_WP_MOTION_PICTURE_API_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


AQSHF_REPOSITORY_CODE = "AL-AQSHF"
AQSHF_ARCHIVE_TYPE = "Institutional film archive"
AQSHF_COUNTRY = normalize_country("Albania")
AQSHF_INSTITUTION_NAME = "Arkivi Qendror Shtetëror i Filmit / The Albanian National Film Archive"
AQSHF_PLATFORM_LABEL = "AQSHF"
AQSHF_WP_PER_PAGE = 100
AQSHF_REQUEST_PAUSE = 0.1

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "sq-AL,sq;q=0.9,en;q=0.8,pt-BR;q=0.7"})

METADATA_LABELS = {
    "reference_code": ("Kodi i referencës", "Reference Code"),
    "title": ("Titulli", "Title"),
    "description": ("Përshkrimi", "Description"),
    "screenwriter": ("Skenari", "Screenwriter", "Scriptwriter"),
    "director": ("Regjisor", "Director"),
    "camera": ("Operator", "Camera"),
    "editing": ("Montazhi", "Edition", "Editing"),
    "sound": ("Zëri", "Sound"),
    "category": ("Kategoria", "Category", "Cathegory"),
    "chroma": ("Kroma", "Chroma"),
    "year": ("Viti i prodhimit", "Year"),
    "reels": ("Numri i akteve", "Reels"),
    "length": ("Kohëzgjatja (në minuta)", "Length (in minutes)"),
    "location": ("Vendi i prodhimit", "Location", "Country"),
    "producer": ("Producenti", "Producer"),
    "notes": ("Shënime", "Notes"),
}


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _strip_html(value, *, limit=None):
    text = BeautifulSoup(html.unescape(str(value or "")), "html.parser").get_text(" ", strip=True)
    return _clean_text(text, limit=limit)


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _metadata_from_table(content_html):
    soup = BeautifulSoup(content_html or "", "html.parser")
    metadata = {}
    for row in soup.find_all("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
        if len(cells) >= 2:
            metadata[_clean_text(cells[0])] = _clean_text(cells[1])
    return metadata


def _metadata_value(metadata, key):
    for label in METADATA_LABELS[key]:
        value = metadata.get(label)
        if value:
            return value
    return ""


def collect_aqshf_institutions():
    return [
        {
            "institution": AQSHF_INSTITUTION_NAME,
            "slug": slugify(AQSHF_INSTITUTION_NAME),
            "country": AQSHF_COUNTRY,
            "continent": country_to_continent(AQSHF_COUNTRY),
            "repository_code": AQSHF_REPOSITORY_CODE,
            "archive_type": AQSHF_ARCHIVE_TYPE,
            "aqshf_detail_url": AQSHF_HOME_URL,
            "external_url": AQSHF_MOTION_PICTURES_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_aqshf_motion_picture_post(post):
    content_html = post.get("content", {}).get("rendered", "")
    metadata = _metadata_from_table(content_html)
    title = (
        _metadata_value(metadata, "title")
        or _strip_html(post.get("title", {}).get("rendered", ""))
        or str(post.get("slug", ""))
    )
    subject = _metadata_value(metadata, "category")
    year = _metadata_value(metadata, "year")
    record_id = _metadata_value(metadata, "reference_code") or str(post.get("id", ""))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro descritivo público do catálogo Motion Pictures do AQSHF; ficha audiovisual sem pressupor player aberto ou download de mídia.",
                f"código de referência: {record_id}" if record_id else "",
                f"direção: {_metadata_value(metadata, 'director')}" if _metadata_value(metadata, "director") else "",
                f"câmera: {_metadata_value(metadata, 'camera')}" if _metadata_value(metadata, "camera") else "",
                f"duração: {_metadata_value(metadata, 'length')}" if _metadata_value(metadata, "length") else "",
                f"croma: {_metadata_value(metadata, 'chroma')}" if _metadata_value(metadata, "chroma") else "",
                f"local: {_metadata_value(metadata, 'location')}" if _metadata_value(metadata, "location") else "",
                f"produtor: {_metadata_value(metadata, 'producer')}" if _metadata_value(metadata, "producer") else "",
                _metadata_value(metadata, "notes"),
                _metadata_value(metadata, "description") or _strip_html(post.get("excerpt", {}).get("rendered", "")),
            ]
            if value
        ),
        limit=1000,
    )
    return {
        "record_id": record_id,
        "source_kind": "wordpress_motion_picture",
        "video_link": post.get("link", ""),
        "platform": AQSHF_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": year or str(post.get("date", ""))[:10],
        "embedded": False,
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": AQSHF_REPOSITORY_CODE,
        "archive_type": AQSHF_ARCHIVE_TYPE,
        "aqshf_detail_url": AQSHF_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": AQSHF_HOME_URL,
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
        "partner_site": AQSHF_HOME_URL,
        "platform": record.get("platform", AQSHF_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_motion_picture_page(page):
    response = _fetch(
        AQSHF_WP_MOTION_PICTURE_API_URL,
        params={
            "per_page": AQSHF_WP_PER_PAGE,
            "page": page,
            "_fields": "id,date,modified,slug,title,link,content,excerpt",
        },
    )
    response.raise_for_status()
    return response


def collect_aqshf_dataset():
    institutions = collect_aqshf_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    page_errors = []
    api_errors = []
    total_expected = 0
    total_pages = 1

    for url, warning in [
        (AQSHF_HOME_URL, "Página oficial do arquivo nacional albanês de filmes."),
        (AQSHF_MOTION_PICTURES_URL, "Listagem pública Motion Pictures usada como evidência de rota catalográfica."),
        (AQSHF_STATISTICS_URL, "Página institucional de estatísticas e descrição do acervo audiovisual."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            page_errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= total_pages:
        try:
            response = _fetch_motion_picture_page(page)
            if page == 1:
                total_expected = _as_int(response.headers.get("X-WP-Total"))
                total_pages = _as_int(response.headers.get("X-WP-TotalPages"), 1)
            posts = response.json()
            records.extend(parse_aqshf_motion_picture_post(post) for post in posts)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(posts),
                    0,
                    f"Página {page} de {total_pages} do endpoint WordPress público `motion_picture`.",
                )
            )
        except Exception as error:
            api_errors.append(f"motion_picture page {page}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{AQSHF_WP_MOTION_PICTURE_API_URL}?per_page={AQSHF_WP_PER_PAGE}&page={page}",
                    "erro",
                    warning="Falha em página do endpoint `motion_picture`; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        page += 1
        if page <= total_pages:
            time.sleep(AQSHF_REQUEST_PAUSE)

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_endpoint = bool(total_expected) and len(video_links) == total_expected and not api_errors
    summary_warning = (
        "Corpus institucional incorporado pelo endpoint público WordPress `motion_picture` do AQSHF. "
        f"A rodada materializou {len(video_links)} de {total_expected or len(video_links)} registros declarados pelo endpoint. "
        "São fichas descritivas de filmes/imagens em movimento; nenhum arquivo de mídia é baixado e a existência de player público aberto não é presumida."
    )
    if not complete_endpoint:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha ou divergência de paginação."

    summary = [
        {
            **_base_row(institution),
            "partner_site": AQSHF_HOME_URL,
            "partner_domain": normalize_domain(AQSHF_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_endpoint else "acessivel" if video_links else "instavel",
            "final_url": AQSHF_MOTION_PICTURES_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_endpoint else "media",
            "warning": summary_warning,
            "error": "; ".join([*page_errors, *api_errors]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "AQSHF_WP_PER_PAGE",
    "collect_aqshf_dataset",
    "collect_aqshf_institutions",
    "parse_aqshf_motion_picture_post",
]
