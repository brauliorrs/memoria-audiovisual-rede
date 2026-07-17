from __future__ import annotations

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    EAFA_ABOUT_URL,
    EAFA_ACCESS_URL,
    EAFA_HOME_URL,
    EAFA_SEARCH_URL,
    EAFA_UEA_PAGE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


EAFA_REPOSITORY_CODE = "GB-EAFA"
EAFA_ARCHIVE_TYPE = "Regional film and television archive"
EAFA_COUNTRY = normalize_country("United Kingdom")
EAFA_INSTITUTION_NAME = "East Anglian Film Archive"
EAFA_PLATFORM_LABEL = "East Anglian Film Archive"
EAFA_VIDEO_SEARCH_URL = f"{EAFA_SEARCH_URL}?hasVideo=on"
EAFA_REQUEST_PAUSE = 0.04

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "en-GB,en;q=0.9,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = requests.get(
        url,
        headers={**SESSION.headers, "Connection": "close"},
        timeout=(15, REQUEST_TIMEOUT),
        allow_redirects=True,
    )
    if response.status_code == 405 and response.headers.get("x-amzn-waf-action") == "captcha":
        response.close()
        raise RuntimeError("Fonte protegida temporariamente por AWS WAF CAPTCHA; coleta automática pausada.")
    response.raise_for_status()
    return response


def _max_pages_from_env():
    value = os.environ.get("EAFA_MAX_PAGES", "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def _max_records_from_env():
    value = os.environ.get("EAFA_MAX_RECORDS", "").strip()
    return int(value) if value.isdigit() and int(value) > 0 else None


def _max_workers_from_env():
    value = os.environ.get("EAFA_MAX_WORKERS", "2").strip()
    return int(value) if value.isdigit() and int(value) > 0 else 2


def _detail_retries_from_env():
    value = os.environ.get("EAFA_DETAIL_RETRIES", "3").strip()
    return int(value) if value.isdigit() and int(value) >= 0 else 3


def _search_page_url(page):
    params = {"hasVideo": "on"}
    if page > 1:
        params["pagination"] = str(page)
    return f"{EAFA_SEARCH_URL}?{urlencode(params)}"


def _extract_work_id(url):
    query = parse_qs(urlparse(str(url)).query)
    values = query.get("id") or []
    if values:
        return _clean_text(values[0])
    return _clean_text(str(url).rstrip("/").rsplit("/", 1)[-1])


def _extract_year(*values):
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
    return match.group(1) if match else ""


def extract_eafa_search_totals(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    page_input = soup.select_one("input.pageNumber")
    total_pages = int(page_input.get("max", "1")) if page_input and str(page_input.get("max", "")).isdigit() else 1
    stats_text = _clean_text(" ".join(item.get_text(" ", strip=True) for item in soup.select(".statistics")))
    match = re.search(r"showing results\s+\d+\s*-\s*\d+\s+of\s+([\d,\.]+)\b", stats_text, flags=re.I)
    if not match:
        matches = re.findall(r"\bof\s+([\d,\.]+)\b", stats_text, flags=re.I)
        match = max(matches, key=lambda value: int(re.sub(r"\D", "", value) or 0), default="")
        return total_pages, int(re.sub(r"\D", "", match) or 0)
    total_records = int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0
    return total_pages, total_records


def parse_eafa_search_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    for item in soup.select("#search-result-items li"):
        anchor = item.select_one('a[href*="/work/"]')
        if not anchor:
            continue
        detail_url = urljoin(page_url, anchor.get("href", ""))
        title_tag = item.select_one("h2.item-title")
        title = _clean_text(title_tag.get_text(" ", strip=True) if title_tag else anchor.get("aria-label", ""))
        meta_spans = [_clean_text(span.get_text(" ", strip=True)) for span in item.select(".item-tile-meta span")]
        date_text = next((value for value in meta_spans if not value.lower().startswith("cat no")), "")
        cat_no_tag = item.select_one(".catno")
        cat_no = _clean_text(cat_no_tag.get_text(" ", strip=True).replace("Cat no.", "")) if cat_no_tag else ""
        main = item.select_one(".item-main")
        location_line = ""
        if main:
            direct_paragraphs = [_clean_text(p.get_text(" ", strip=True)) for p in main.find_all("p", recursive=False)]
            location_line = direct_paragraphs[0] if direct_paragraphs else ""
        summary_tag = item.select_one(".override-summary")
        side_values = [_clean_text(p.get_text(" ", strip=True)) for p in item.select(".canHide p")]
        duration = side_values[1] if len(side_values) > 1 else ""
        colour_sound = side_values[2] if len(side_values) > 2 else ""
        record_id = _extract_work_id(detail_url)
        records.append(
            {
                "record_id": record_id,
                "detail_url": detail_url,
                "title": title,
                "date": date_text,
                "cat_no": cat_no,
                "location_line": location_line,
                "summary": _clean_text(summary_tag.get_text(" ", strip=True) if summary_tag else "", limit=900),
                "duration": duration,
                "colour_sound": colour_sound,
            }
        )
    return records


def _extract_work_details(soup):
    details = {}
    for item in soup.select(".work-details li"):
        label_tag = item.find("span")
        if not label_tag:
            continue
        label = _clean_text(label_tag.get_text(" ", strip=True)).rstrip(":")
        text = _clean_text(item.get_text(" ", strip=True))
        value = _clean_text(re.sub(rf"^{re.escape(label)}:?\s*", "", text))
        details[label] = value
    return details


def _extract_heading_date_location(soup):
    title = _clean_text(soup.find("h1").get_text(" ", strip=True) if soup.find("h1") else "")
    h2 = soup.find("h2")
    heading = _clean_text(h2.get_text(" ", strip=True) if h2 else "")
    return title, heading


def _extract_overview_sections(soup):
    overview = soup.select_one("#overview")
    if not overview:
        return "", "", ""
    lead = _clean_text(overview.select_one("p.lead").get_text(" ", strip=True) if overview.select_one("p.lead") else "")
    paragraphs = []
    keywords = ""
    for element in overview.children:
        name = getattr(element, "name", "")
        if name == "h2" and _clean_text(element.get_text(" ", strip=True)).lower() == "keywords":
            sibling = element.find_next_sibling()
            keywords = _clean_text(sibling.get_text(" ", strip=True) if sibling else "")
            continue
        if name == "p" and "lead" not in (element.get("class") or []):
            paragraphs.append(_clean_text(element.get_text(" ", strip=True)))
    description = _clean_text(" ".join(value for value in paragraphs if value), limit=1600)
    return lead, description, keywords


def parse_eafa_work_page(html_text, page_url, search_record=None):
    search_record = search_record or {}
    soup = BeautifulSoup(html_text or "", "html.parser")
    iframe_sources = [
        urljoin(page_url, tag.get("src", ""))
        for tag in soup.select("iframe[src]")
        if _clean_text(tag.get("src", ""))
    ]
    video_sources = re.findall(r"https?://[^\"'\s<>]+?(?:\.mp4|\.m3u8)(?:[?&][^\"'\s<>]+)?", html_text or "", flags=re.I)
    media_sources = list(dict.fromkeys([*iframe_sources, *video_sources]))
    if not media_sources:
        return None

    title, heading = _extract_heading_date_location(soup)
    details = _extract_work_details(soup)
    lead, overview, keywords = _extract_overview_sections(soup)
    cat_no = _clean_text((soup.select_one("p.date") or "").get_text(" ", strip=True) if soup.select_one("p.date") else "")
    cat_no = _clean_text(cat_no.replace("Cat no.", "")) or search_record.get("cat_no", "")
    date = _extract_year(heading, search_record.get("date", ""))
    subject = _clean_text(
        "; ".join(
            value
            for value in [
                details.get("Category", ""),
                details.get("Genre", ""),
                details.get("Work Type", ""),
                details.get("Subject", ""),
                keywords,
            ]
            if value
        ),
        limit=900,
    )
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do catálogo EAFA com player de web video embutido.",
                f"Cat no.: {cat_no}" if cat_no else "",
                f"data/local: {heading}" if heading else search_record.get("location_line", ""),
                f"duração/suporte: {search_record.get('duration', '')}" if search_record.get("duration") else "",
                f"características visuais/sonoras: {search_record.get('colour_sound', '')}" if search_record.get("colour_sound") else "",
                f"categoria: {details.get('Category', '')}" if details.get("Category") else "",
                f"gênero: {details.get('Genre', '')}" if details.get("Genre") else "",
                f"tipo de obra: {details.get('Work Type', '')}" if details.get("Work Type") else "",
                f"locais: {details.get('Locations', '')}" if details.get("Locations") else "",
                lead or search_record.get("summary", ""),
                overview,
                f"palavras-chave: {keywords}" if keywords else "",
                "Mídia não baixada; link público de ficha e player registrado para observação.",
            ]
            if value
        ),
        limit=2200,
    )
    return {
        "record_id": search_record.get("record_id") or _extract_work_id(page_url),
        "source_kind": "eafa_public_catalogue_video",
        "video_link": page_url,
        "page_url": page_url,
        "platform": EAFA_PLATFORM_LABEL,
        "title": title or search_record.get("title", ""),
        "subject": subject,
        "description": description,
        "date": date or search_record.get("date", ""),
        "embedded": bool(media_sources),
        "media_sources": media_sources,
        "cat_no": cat_no,
    }


def collect_eafa_institutions():
    return [
        {
            "institution": EAFA_INSTITUTION_NAME,
            "slug": slugify(EAFA_INSTITUTION_NAME),
            "country": EAFA_COUNTRY,
            "continent": country_to_continent(EAFA_COUNTRY),
            "repository_code": EAFA_REPOSITORY_CODE,
            "archive_type": EAFA_ARCHIVE_TYPE,
            "eafa_detail_url": EAFA_HOME_URL,
            "external_url": EAFA_HOME_URL,
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
        "repository_code": EAFA_REPOSITORY_CODE,
        "archive_type": EAFA_ARCHIVE_TYPE,
        "eafa_detail_url": EAFA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": EAFA_VIDEO_SEARCH_URL,
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
        "partner_site": EAFA_VIDEO_SEARCH_URL,
        "platform": record.get("platform", EAFA_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_eafa_dataset(max_pages=None, max_records=None):
    institutions = collect_eafa_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    search_records_by_id = {}
    video_records_by_id = {}
    max_pages = max_pages or _max_pages_from_env()
    max_records = max_records or _max_records_from_env()
    total_pages = 1
    announced_total = 0
    pages_read = 0
    skipped_without_player = 0

    contextual_pages = [
        (EAFA_HOME_URL, "Página oficial do EAFA; declara o arquivo regional e a busca pública."),
        (EAFA_ACCESS_URL, "Página de acesso; informa mais de 200 horas de filmes disponíveis no site e limites de digitalização."),
        (EAFA_ABOUT_URL, "Página institucional; descreve filmes, televisão, vídeos e imagens em movimento preservados pelo EAFA."),
        (EAFA_UEA_PAGE_URL, "Página da University of East Anglia; confirma vínculo institucional, coleção e catálogo online."),
    ]
    for url, warning in contextual_pages:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= total_pages:
        if max_pages and page > max_pages:
            break
        try:
            page_url = _search_page_url(page)
            response = _fetch(page_url)
            page_total, page_announced_total = extract_eafa_search_totals(response.text)
            total_pages = max(total_pages, page_total)
            announced_total = max(announced_total, page_announced_total)
            page_records = parse_eafa_search_page(response.text, response.url)
            for record in page_records:
                search_records_by_id.setdefault(record["record_id"], record)
            pages_read += 1
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    len(page_records),
                    f"Página {page} de {total_pages} da busca EAFA com `hasVideo=on`; total anunciado: {announced_total}.",
                )
            )
            page += 1
            time.sleep(EAFA_REQUEST_PAUSE)
        except Exception as error:
            errors.append(f"search page {page}: {error}")
            internal_pages.append(_internal_page_row(institution, _search_page_url(page), "erro", warning="Falha em página da busca EAFA.", error=str(error)))
            break

    if pages_read == 0:
        raise RuntimeError(
            "Coleta EAFA interrompida antes da escrita: nenhuma página da busca pública foi lida. "
            + " | ".join(errors[:5])
        )

    detail_records = list(search_records_by_id.values())
    if max_records:
        detail_records = detail_records[:max_records]

    def collect_detail_record(search_record):
        retries = _detail_retries_from_env()
        last_error = None
        for attempt in range(retries + 1):
            try:
                response = _fetch(search_record["detail_url"])
                try:
                    record = parse_eafa_work_page(response.text, response.url, search_record)
                    response_url = response.url
                    status_code = response.status_code
                finally:
                    response.close()
                break
            except Exception as error:
                last_error = error
                if attempt < retries:
                    time.sleep(min(1.5 * (attempt + 1), 6))
                    continue
                return (
                    None,
                    _internal_page_row(
                        institution,
                        search_record["detail_url"],
                        "erro",
                        warning="Falha ao abrir ficha pública EAFA.",
                        error=str(last_error),
                    ),
                    f"{search_record['detail_url']}: {last_error}",
                    False,
                )

        try:
            if not record:
                return (
                    None,
                    _internal_page_row(
                        institution,
                        response_url,
                        "sem_player",
                        status_code,
                        0,
                        0,
                        "Ficha listada em busca com web video, mas sem player detectável no HTML da rodada.",
                    ),
                    None,
                    True,
                )
            return (
                record,
                _internal_page_row(
                    institution,
                    response_url,
                    "ok",
                    status_code,
                    1,
                    int(record.get("embedded", False)),
                    "Ficha pública EAFA com player de web video confirmado.",
                ),
                None,
                False,
            )
        except Exception as error:
            return (
                None,
                _internal_page_row(
                    institution,
                    search_record["detail_url"],
                    "erro",
                    warning="Falha ao abrir ficha pública EAFA.",
                    error=str(error),
                ),
                f"{search_record['detail_url']}: {error}",
                False,
            )

    max_workers = min(_max_workers_from_env(), max(1, len(detail_records)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(collect_detail_record, search_record) for search_record in detail_records]
        for future in as_completed(futures):
            record, internal_page, error, skipped = future.result()
            internal_pages.append(internal_page)
            if skipped:
                skipped_without_player += 1
            if error:
                errors.append(error)
            if record:
                video_records_by_id.setdefault(record["record_id"], record)

    records = list(video_records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    full_search_read = pages_read == total_pages and not max_pages
    complete_catalogue = full_search_read and announced_total and len(video_links) == announced_total and not errors
    integrity_status = "integro" if complete_catalogue else "acessivel" if video_links else "instavel"
    warning = (
        "Corpus EAFA incorporado pela busca pública `hasVideo=on` do catálogo oficial. "
        f"A busca anunciou {announced_total or 'total não detectado'} registros com web video em {total_pages} páginas; "
        f"a rodada leu {pages_read} páginas, encontrou {len(search_records_by_id)} fichas candidatas e confirmou {len(video_links)} players. "
        "Entram apenas fichas com player público detectável; nenhum arquivo de mídia é baixado."
    )
    if skipped_without_player:
        warning += f" Fichas sem player detectável na rodada: {skipped_without_player}."
    if max_pages:
        warning += f" Rodada limitada por EAFA_MAX_PAGES={max_pages}."
    if max_records:
        warning += f" Rodada limitada por EAFA_MAX_RECORDS={max_records}."
    if errors:
        warning += " Erros: " + " | ".join(errors[:5])

    summary = [
        {
            **_base_row(institution),
            "partner_site": EAFA_VIDEO_SEARCH_URL,
            "partner_domain": normalize_domain(EAFA_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": integrity_status,
            "final_url": EAFA_VIDEO_SEARCH_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if integrity_status == "integro" else "media" if video_links else "alta",
            "warning": warning,
            "error": " | ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "EAFA_ARCHIVE_TYPE",
    "EAFA_INSTITUTION_NAME",
    "EAFA_PLATFORM_LABEL",
    "EAFA_REPOSITORY_CODE",
    "collect_eafa_dataset",
    "collect_eafa_institutions",
    "extract_eafa_search_totals",
    "parse_eafa_search_page",
    "parse_eafa_work_page",
]
