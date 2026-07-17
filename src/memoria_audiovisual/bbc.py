import json
import re
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    BBC_ARCHIVE_ACCESS_URL,
    BBC_ARCHIVE_DOWNLOADER_URL,
    BBC_ARCHIVE_HOME_URL,
    BBC_ARCHIVE_REWIND_URL,
    BBC_ARCHIVE_SEARCH_URL,
    BBC_ARCHIVE_SERVICES_URL,
    BBC_ARCHIVE_TOPIC_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


BBC_REPOSITORY_CODE = "GB-BBC-ARCHIVE"
BBC_ARCHIVE_TYPE = "Broadcast audiovisual archive"
BBC_COUNTRY = normalize_country("United Kingdom")
BBC_INSTITUTION_NAME = "BBC Archive"
BBC_PLATFORM_LABEL = "BBC Archive"

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "en-GB,en;q=0.9,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _extract_initial_data(html_text):
    match = re.search(r'window\.__INITIAL_DATA__=("(?:\\.|[^"\\])*")\s*;', html_text or "")
    if not match:
        return {}
    try:
        return json.loads(json.loads(match.group(1)))
    except Exception:
        return {}


def _max_page_from_html(html_text):
    page_numbers = [int(value) for value in re.findall(r"\?page=(\d+)", html_text or "")]
    return max(page_numbers) if page_numbers else 1


def _group_title(component_key):
    query = parse_qs(urlparse("?" + str(component_key or "").split("?", 1)[-1]).query)
    values = query.get("title") or []
    return unquote(values[0]).strip() if values else ""


def _format_duration(milliseconds, fallback=""):
    try:
        seconds = int(milliseconds or 0) // 1000
    except (TypeError, ValueError):
        seconds = 0
    if not seconds:
        match = re.search(r"(?:Video|Audio),\s*([0-9:]+)", fallback or "")
        return match.group(1) if match else ""
    minutes, second = divmod(seconds, 60)
    hour, minute = divmod(minutes, 60)
    return f"{hour:02d}:{minute:02d}:{second:02d}" if hour else f"{minute:02d}:{second:02d}"


def _extract_year(*values):
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    return match.group(1) if match else ""


def _is_video_promo(promo):
    indicator = promo.get("pageTypeIndicator") or {}
    return promo.get("type") == "video" or str(indicator.get("altText", "")).startswith("Video")


def _iter_video_promos(payload):
    for component_key, component in (payload.get("data") or {}).items():
        group = _group_title(component_key)
        for promo in (component.get("data") or {}).get("promos") or []:
            url = promo.get("url", "")
            if not str(url).startswith("/videos/") or not _is_video_promo(promo):
                continue
            yield group, promo


def collect_bbc_institutions():
    return [
        {
            "institution": BBC_INSTITUTION_NAME,
            "slug": slugify(BBC_INSTITUTION_NAME),
            "country": BBC_COUNTRY,
            "continent": country_to_continent(BBC_COUNTRY),
            "repository_code": BBC_REPOSITORY_CODE,
            "archive_type": BBC_ARCHIVE_TYPE,
            "bbc_detail_url": BBC_ARCHIVE_HOME_URL,
            "external_url": BBC_ARCHIVE_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_bbc_video_promo(promo, group_title="", page_number=1):
    indicator = promo.get("pageTypeIndicator") or {}
    metadata_items = promo.get("metadataStripItems") or []
    metadata_text = "; ".join(
        _clean_text(f"{item.get('label', '')}: {item.get('text', '')}")
        for item in metadata_items
        if _clean_text(item.get("text", ""))
    )
    title = _clean_text(promo.get("headline") or promo.get("contentTitle"))
    description = _clean_text(promo.get("description") or "")
    page_url = urljoin(BBC_ARCHIVE_HOME_URL, promo.get("url", ""))
    record_id = str(promo.get("urn") or "").rsplit(":", 1)[-1] or page_url.rstrip("/").rsplit("/", 1)[-1]
    duration = _format_duration(promo.get("duration"), indicator.get("altText", ""))
    image = promo.get("image") or {}
    image_alt = _clean_text(image.get("alt", ""))
    year = _extract_year(title, description, promo.get("lastPublished", ""))
    note = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do tópico BBC Archive.",
                f"grupo: {group_title}" if group_title else "",
                f"duração: {duration}" if duration else "",
                metadata_text,
                f"imagem: {image_alt}" if image_alt else "",
                description,
            ]
            if value
        ),
        limit=1000,
    )
    return {
        "record_id": record_id,
        "source_kind": "bbc_topic_promo",
        "video_link": page_url,
        "page_url": page_url,
        "platform": BBC_PLATFORM_LABEL,
        "title": title,
        "subject": group_title,
        "description": note,
        "date": year or str(promo.get("lastPublished", ""))[:10],
        "page_number": page_number,
        "embedded": True,
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": BBC_REPOSITORY_CODE,
        "archive_type": BBC_ARCHIVE_TYPE,
        "bbc_detail_url": BBC_ARCHIVE_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": BBC_ARCHIVE_TOPIC_URL,
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
        "partner_site": BBC_ARCHIVE_TOPIC_URL,
        "platform": record.get("platform", BBC_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_bbc_dataset():
    institutions = collect_bbc_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_url = {}
    errors = []
    max_page = 1

    contextual_pages = [
        (BBC_ARCHIVE_HOME_URL, "Página pública BBC Archive; redireciona para o tópico curatorial coletado."),
        (BBC_ARCHIVE_ACCESS_URL, "Página oficial de acesso não comercial; contexto metodológico, não corpus coletado."),
        (BBC_ARCHIVE_SEARCH_URL, "Archive Search; ferramenta separada, não tratada como corpus público aberto."),
        (BBC_ARCHIVE_SERVICES_URL, "Archive Services; serviço para produtores com registro, não corpus público aberto."),
        (BBC_ARCHIVE_REWIND_URL, "BBC Rewind; superfície geobloqueada fora do Reino Unido na rodada."),
        (BBC_ARCHIVE_DOWNLOADER_URL, "Archive Downloader; rota com licença RemArc e aceite de termos, não usada como base desta coleta."),
    ]
    for url, warning in contextual_pages:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= max_page:
        url = BBC_ARCHIVE_TOPIC_URL if page == 1 else f"{BBC_ARCHIVE_TOPIC_URL}?page={page}"
        try:
            response = _fetch(url)
            response.raise_for_status()
            if page == 1:
                max_page = _max_page_from_html(response.text)
            payload = _extract_initial_data(response.text)
            page_records = [
                parse_bbc_video_promo(promo, group_title=group_title, page_number=page)
                for group_title, promo in _iter_video_promos(payload)
            ]
            page_unique = {}
            for record in page_records:
                page_unique.setdefault(record["video_link"], record)
                records_by_url.setdefault(record["video_link"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_unique),
                    len(page_unique),
                    f"Página {page} de {max_page} do tópico público BBC Archive; apenas promos rotulados como vídeo entram no corpus.",
                )
            )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    url,
                    "erro",
                    warning="Falha em página paginada do tópico BBC Archive; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        page += 1

    records = list(records_by_url.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_topic = bool(records) and not errors and page > max_page
    summary_warning = (
        "Corpus institucional incorporado pelo tópico público BBC Archive (`/topics/c01yxyz46myt`). "
        f"A rodada percorreu {max_page} páginas públicas e materializou {len(video_links)} registros rotulados como vídeo. "
        "O recorte não equivale ao acervo total da BBC, ao Archive Search, ao BBC Rewind geobloqueado ou a serviços com registro/licença."
    )
    if not complete_topic:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha de paginação."

    summary = [
        {
            **_base_row(institution),
            "partner_site": BBC_ARCHIVE_TOPIC_URL,
            "partner_domain": normalize_domain(BBC_ARCHIVE_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_topic else "acessivel" if video_links else "instavel",
            "final_url": BBC_ARCHIVE_TOPIC_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": len(video_links),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_topic else "media",
            "warning": summary_warning,
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "BBC_PLATFORM_LABEL",
    "collect_bbc_dataset",
    "collect_bbc_institutions",
    "parse_bbc_video_promo",
]
