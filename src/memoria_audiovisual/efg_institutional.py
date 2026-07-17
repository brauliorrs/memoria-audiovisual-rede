from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from urllib.parse import quote, unquote, urljoin

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


EFG_DETAIL_LABELS = {
    "Collection:",
    "Colour:",
    "Date:",
    "Description:",
    "Director:",
    "Document type:",
    "Genre:",
    "Keywords:",
    "Language:",
    "Other title(s):",
    "Production company:",
    "Provider:",
    "Rights:",
    "Runtime:",
    "Sound:",
    "Year:",
}


@dataclass(frozen=True)
class EfgInstitutionalCorpusConfig:
    code: str
    institution_name: str
    repository_code: str
    archive_type: str
    country: str
    detail_url_field: str
    home_url: str
    search_url: str
    detail_prefix: str
    context_urls: list[tuple[str, str]] = field(default_factory=list)
    external_url: str = ""
    platform_label: str = "European Film Gateway"
    accept_language: str = "en;q=0.9,pt-BR;q=0.7"
    max_search_pages: int = 30
    request_pause: float = 0.05
    description_limit: int = 1400
    summary_note: str = ""
    scope_note: str = ""


def clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def build_efg_session(accept_language):
    session = requests.Session()
    session.headers.update({**HEADERS, "Accept-Language": accept_language})
    return session


def fetch_url(session, url, attempts=3):
    last_error = None
    for attempt in range(attempts):
        try:
            response = session.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=False)
            if response.is_redirect:
                location = urljoin(response.url, response.headers.get("Location", ""))
                if "/validate-browser" in location:
                    validation = session.get(location, timeout=(8, REQUEST_TIMEOUT), allow_redirects=False)
                    location = urljoin(validation.url, validation.headers.get("Location", url))
                response = session.get(location, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
            response.raise_for_status()
            return response
        except requests.RequestException as error:
            last_error = error
            if attempt < attempts - 1:
                time.sleep(0.5 * (attempt + 1))
    raise last_error


def efg_search_page_url(search_url, page_index):
    if page_index <= 0:
        return search_url
    separator = "&" if "?" in search_url else "?"
    return f"{search_url}{separator}page={page_index}%2C0%2C0"


def extract_efg_result_total(html):
    text = BeautifulSoup(html or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"Videos?\s*\(([\d,\.]+)\s+Results?\)", text, flags=re.IGNORECASE)
    if not match:
        return 0
    return int(re.sub(r"\D", "", match.group(1)) or 0)


def parse_efg_search_page(html, page_url, detail_prefix):
    soup = BeautifulSoup(html or "", "html.parser")
    detail_urls = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "").split(";jsessionid=", 1)[0]
        absolute_url = urljoin(page_url, href)
        if "/detail/" in absolute_url and detail_prefix in absolute_url:
            detail_urls.append(absolute_url)
    return list(dict.fromkeys(detail_urls))


def extract_efg_record_id(url, detail_prefix):
    if detail_prefix in str(url):
        return str(url).rsplit(detail_prefix, 1)[-1].split("?", 1)[0]
    return quote(str(url).rstrip("/").rsplit("/", 1)[-1])


def extract_efg_metadata(lines):
    metadata = {}
    for index, line in enumerate(lines):
        if line not in EFG_DETAIL_LABELS:
            continue
        values = []
        next_index = index + 1
        while next_index < len(lines):
            next_line = lines[next_index]
            if next_line in EFG_DETAIL_LABELS or next_line in {"Related Names", "View as PDF", "Secondary links english"}:
                break
            if next_line.startswith("View at "):
                break
            values.append(next_line)
            next_index += 1
        metadata[line.rstrip(":")] = clean_text(" ".join(values))
    return metadata


def extract_efg_player_source(soup):
    video = soup.find("video")
    if not video or not video.get("data-setup"):
        return ""
    try:
        setup = json.loads(video["data-setup"])
    except Exception:
        return ""
    sources = setup.get("sources") or []
    if not sources:
        return ""
    return clean_text(sources[0].get("src", ""))


def extract_efg_external_view_url(soup, page_url):
    for anchor in soup.select("a[href]"):
        label = clean_text(anchor.get_text(" ", strip=True))
        if label.startswith("View at "):
            return urljoin(page_url, anchor["href"])
    return ""


def has_efg_player_shell(html, text):
    normalized = str(html or "").lower()
    text_normalized = str(text or "").lower()
    return "video-js" in normalized or "supports html5 video" in text_normalized or "enable javascript" in text_normalized


def parse_efg_detail_page(html, page_url, config):
    soup = BeautifulSoup(html or "", "html.parser")
    lines = [clean_text(line) for line in soup.get_text("\n", strip=True).split("\n")]
    lines = [line for line in lines if line]
    text = " ".join(lines)
    metadata = extract_efg_metadata(lines)
    title_tag = soup.find("h1")
    title = clean_text(title_tag.get_text(" ", strip=True) if title_tag else "")
    media_source_url = extract_efg_player_source(soup)
    external_view_url = extract_efg_external_view_url(soup, page_url)
    has_player_shell = has_efg_player_shell(html, text)
    description = clean_text(
        " | ".join(
            value
            for value in [
                f"Ficha pública de {config.institution_name} no European Film Gateway.",
                "player EFG sinalizado no HTML, sem fonte de mídia materializada na coleta estática"
                if has_player_shell and not media_source_url
                else "",
                f"título alternativo: {metadata.get('Other title(s)', '')}" if metadata.get("Other title(s)") else "",
                f"gênero: {metadata.get('Genre', '')}" if metadata.get("Genre") else "",
                f"duração: {metadata.get('Runtime', '')}" if metadata.get("Runtime") else "",
                f"coleção: {metadata.get('Collection', '')}" if metadata.get("Collection") else "",
                f"direção: {metadata.get('Director', '')}" if metadata.get("Director") else "",
                f"produtora: {metadata.get('Production company', '')}" if metadata.get("Production company") else "",
                f"cor: {metadata.get('Colour', '')}" if metadata.get("Colour") else "",
                f"som: {metadata.get('Sound', '')}" if metadata.get("Sound") else "",
                f"direitos: {metadata.get('Rights', '')}" if metadata.get("Rights") else "",
                f"fonte de mídia: {media_source_url}" if media_source_url else "",
                f"ver também: {external_view_url}" if external_view_url else "",
                metadata.get("Description", ""),
            ]
            if value
        ),
        limit=config.description_limit,
    )
    return {
        "record_id": extract_efg_record_id(page_url, config.detail_prefix),
        "title": title,
        "detail_url": page_url,
        "media_source_url": media_source_url,
        "external_view_url": external_view_url,
        "genre": metadata.get("Genre", ""),
        "keywords": metadata.get("Keywords", ""),
        "year": metadata.get("Year", ""),
        "runtime": metadata.get("Runtime", ""),
        "provider": metadata.get("Provider", ""),
        "rights": metadata.get("Rights", ""),
        "description": description,
        "has_public_player": bool(media_source_url),
        "has_player_shell": has_player_shell,
        "detail_fetch_status": "ok",
    }


def build_efg_detail_fallback_record(detail_url, config, error):
    title_segment = str(detail_url).split("/detail/", 1)[-1].split(f"/{config.detail_prefix}", 1)[0]
    title = clean_text(unquote(title_segment).replace("+", " "))
    return {
        "record_id": extract_efg_record_id(detail_url, config.detail_prefix),
        "title": title or "Registro EFG sem título aberto",
        "detail_url": detail_url,
        "media_source_url": "",
        "external_view_url": "",
        "genre": "",
        "keywords": "",
        "year": "",
        "runtime": "",
        "provider": config.institution_name,
        "rights": "",
        "description": clean_text(
            f"URL pública listada pelo European Film Gateway para {config.institution_name}; "
            f"a ficha de detalhe não foi aberta nesta coleta ({error}).",
            limit=config.description_limit,
        ),
        "has_public_player": False,
        "has_player_shell": False,
        "detail_fetch_status": "erro",
    }


def collect_efg_institutional_institutions(config):
    country = normalize_country(config.country)
    return [
        {
            "institution": config.institution_name,
            "slug": slugify(config.institution_name),
            "country": country,
            "continent": country_to_continent(country),
            "repository_code": config.repository_code,
            "archive_type": config.archive_type,
            config.detail_url_field: config.home_url,
            "external_url": config.external_url or config.search_url,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def base_efg_row(config, institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": config.repository_code,
        "archive_type": config.archive_type,
        config.detail_url_field: config.home_url,
        "content_available_in_source": True,
        "website_available": True,
    }


def efg_internal_page_row(config, institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **base_efg_row(config, institution),
        "partner_site": config.search_url,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def efg_record_to_video_row(config, institution, record):
    subject = clean_text(" | ".join(value for value in [record.get("genre"), record.get("keywords")] if value))
    return {
        **base_efg_row(config, institution),
        "partner_site": config.search_url,
        "platform": config.platform_label,
        "video_link": record.get("detail_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": subject,
        "video_description": record.get("description", ""),
        "video_published_at": record.get("year", ""),
    }


def collect_efg_institutional_dataset(config):
    session = build_efg_session(config.accept_language)
    institutions = collect_efg_institutional_institutions(config)
    institution = institutions[0]
    internal_pages = []
    discovered_detail_urls = []
    records = []
    context_errors = []
    page_errors = []
    detail_errors = []
    announced_total = 0

    for url, warning in config.context_urls:
        try:
            response = fetch_url(session, url)
            internal_pages.append(efg_internal_page_row(config, institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            context_errors.append(f"{url}: {error}")
            internal_pages.append(efg_internal_page_row(config, institution, url, "erro", warning=warning, error=str(error)))

    for page_index in range(config.max_search_pages):
        search_url = efg_search_page_url(config.search_url, page_index)
        try:
            response = fetch_url(session, search_url)
            if page_index == 0:
                announced_total = extract_efg_result_total(response.text)
            detail_urls = parse_efg_search_page(response.text, response.url, config.detail_prefix)
            if not detail_urls and page_index > 0:
                break
            discovered_detail_urls.extend(detail_urls)
            internal_pages.append(
                efg_internal_page_row(
                    config,
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(detail_urls),
                    len(detail_urls),
                    (
                        f"Página {page_index + 1} da coleção {config.institution_name} no EFG; "
                        f"{announced_total or 'total não detectado'} resultados de vídeo anunciados."
                    ),
                )
            )
        except Exception as error:
            page_errors.append(f"{search_url}: {error}")
            internal_pages.append(efg_internal_page_row(config, institution, search_url, "erro", error=str(error)))

    discovered_detail_urls = list(dict.fromkeys(discovered_detail_urls))
    for detail_url in discovered_detail_urls:
        try:
            response = fetch_url(session, detail_url)
            record = parse_efg_detail_page(response.text, response.url, config)
            records.append(record)
            internal_pages.append(
                efg_internal_page_row(
                    config,
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    int(record.get("has_player_shell", False)),
                    f"Ficha pública de vídeo de {config.institution_name} no EFG, com metadados audiovisuais.",
                )
            )
        except Exception as error:
            detail_errors.append(f"{detail_url}: {error}")
            records.append(build_efg_detail_fallback_record(detail_url, config, error))
            internal_pages.append(
                efg_internal_page_row(
                    config,
                    institution,
                    detail_url,
                    "erro",
                    warning=f"Falha ao abrir ficha pública de {config.institution_name} no EFG.",
                    error=str(error),
                )
            )
        time.sleep(config.request_pause)

    video_links = [efg_record_to_video_row(config, institution, record) for record in records]
    complete_detail_total = sum(1 for record in records if record.get("detail_fetch_status") == "ok")
    found_complete = bool(records) and len(records) == len(discovered_detail_urls) and not page_errors and not detail_errors
    total_matches_interface = not announced_total or len(records) >= announced_total
    integrity_status = "integro" if found_complete and total_matches_interface else "acessivel" if video_links else "instavel"
    player_shell_total = sum(1 for record in records if record.get("has_player_shell"))
    summary_warning = (
        f"{config.summary_note} O EFG anunciou {announced_total or 'total não detectado'} resultados de vídeo; "
        f"a rodada registrou {len(records)} URLs {config.detail_prefix} de "
        f"{len(discovered_detail_urls)} URLs de detalhe encontradas, com {complete_detail_total} fichas abertas. "
        f"{config.scope_note} "
        "Nenhum arquivo de mídia é baixado."
    ).strip()
    if announced_total and len(records) != announced_total:
        summary_warning = (
            f"{summary_warning} A divergência entre total anunciado e fichas do prefixo custodial "
            f"{config.detail_prefix} fica registrada como limite da superfície EFG, não como totalidade do arquivo."
        )
    if context_errors:
        summary_warning = f"{summary_warning} Foram registrados {len(context_errors)} problemas em páginas contextuais."
    if not found_complete:
        summary_warning = f"{summary_warning} A completude deve ser lida com cautela por falha de paginação ou ficha."

    summary = [
        {
            **base_efg_row(config, institution),
            "partner_site": config.search_url,
            "partner_domain": normalize_domain(config.search_url),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": integrity_status,
            "final_url": config.search_url,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": player_shell_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if integrity_status == "integro" else "media" if video_links else "alta",
            "warning": summary_warning,
            "error": "; ".join([*context_errors, *page_errors, *detail_errors]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "EFG_DETAIL_LABELS",
    "EfgInstitutionalCorpusConfig",
    "clean_text",
    "collect_efg_institutional_dataset",
    "collect_efg_institutional_institutions",
    "extract_efg_result_total",
    "parse_efg_detail_page",
    "parse_efg_search_page",
]
