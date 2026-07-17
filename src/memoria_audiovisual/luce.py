from __future__ import annotations

import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    LUCE_CATALOG_FILMS_PAGE_URL_TEMPLATE,
    LUCE_CATALOG_FILMS_URL,
    LUCE_CATALOG_HOME_URL,
    LUCE_CINEMATIC_ARCHIVE_URL,
    LUCE_CINECITTA_ARCHIVE_URL,
    LUCE_HOME_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


LUCE_REPOSITORY_CODE = "IT-CINECITTA-LUCE"
LUCE_ARCHIVE_TYPE = "Historical film and audiovisual archive"
LUCE_COUNTRY = normalize_country("Italy")
LUCE_INSTITUTION_NAME = "Cinecittà - Archivio Luce"
LUCE_PLATFORM_LABEL = "Archivio Luce"
LUCE_MAX_RESULT_PAGES = 3
LUCE_DETAIL_WORKERS = 4
LUCE_REQUEST_PAUSE = 0.12
LUCE_CATALOG_BASE_URL = "https://patrimonio.archivioluce.com"

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7"})

DETAIL_LABELS = [
    "data",
    "durata",
    "colore",
    "sonoro",
    "codice filmato",
    "regia di",
    "edizione lingua",
    "nazionalità",
    "Casa di produzione",
]


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    return SESSION.get(url, timeout=(10, REQUEST_TIMEOUT + 10), allow_redirects=True)


def _meta_content(soup, property_name):
    tag = soup.find("meta", attrs={"property": property_name}) or soup.find("meta", attrs={"name": property_name})
    return _clean_text(tag.get("content", "")) if tag else ""


def _extract_record_id(url):
    match = re.search(r"/detail/([^/]+)/", str(url or ""))
    return match.group(1) if match else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def extract_luce_video_files(html_text):
    files = re.findall(
        r"https?://[^\"'\s<>]+?(?:\.m3u8|\.mp4)(?:/playlist\.m3u8)?|rtmp://[^\"'\s<>]+",
        str(html_text or ""),
        flags=re.IGNORECASE,
    )
    return list(dict.fromkeys(_clean_text(file) for file in files if _clean_text(file)))


def _preferred_video_link(files, page_url):
    for suffix in (".m3u8", ".mp4"):
        for file_url in files:
            if suffix in file_url.lower() and file_url.lower().startswith("http"):
                return file_url
    return page_url


def _extract_labeled_value(text, label):
    stop_labels = [item for item in DETAIL_LABELS if item != label]
    stop_pattern = "|".join(re.escape(item) for item in stop_labels)
    pattern = (
        rf"\b{re.escape(label)}\s*:\s*(.*?)"
        rf"(?=\s+(?:{stop_pattern})\s*:|\s+(?:sequenze|keywords|torna alla ricerca|aggiungi ai preferiti|condividi|copia il link|Top)\b|$)"
    )
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return _clean_text(match.group(1), limit=500) if match else ""


def _extract_section(text, start_label, stop_labels):
    stop_pattern = "|".join(re.escape(item) for item in stop_labels)
    match = re.search(rf"\b{re.escape(start_label)}\b\s*(.*?)(?=\s+(?:{stop_pattern})\b|$)", text, flags=re.IGNORECASE)
    return _clean_text(match.group(1), limit=900) if match else ""


def collect_luce_institutions():
    return [
        {
            "institution": LUCE_INSTITUTION_NAME,
            "slug": slugify(LUCE_INSTITUTION_NAME),
            "country": LUCE_COUNTRY,
            "continent": country_to_continent(LUCE_COUNTRY),
            "repository_code": LUCE_REPOSITORY_CODE,
            "archive_type": LUCE_ARCHIVE_TYPE,
            "luce_detail_url": LUCE_HOME_URL,
            "external_url": LUCE_CATALOG_FILMS_URL,
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
        "repository_code": LUCE_REPOSITORY_CODE,
        "archive_type": LUCE_ARCHIVE_TYPE,
        "luce_detail_url": LUCE_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": LUCE_CATALOG_FILMS_URL,
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
        "partner_site": LUCE_CATALOG_FILMS_URL,
        "platform": LUCE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def parse_luce_search_page(html_text, page_url=LUCE_CATALOG_FILMS_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for item in soup.select("div.singolo-risultato"):
        anchor = item.select_one('a[href*="/luce-web/detail/"]')
        if not anchor:
            continue
        href = anchor.get("href", "")
        if "${" in href:
            continue
        detail_url = urljoin(LUCE_CATALOG_BASE_URL, href)
        record_id = _extract_record_id(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        files = extract_luce_video_files(str(item))
        records.append(
            {
                "record_id": record_id,
                "page_url": detail_url,
                "list_text": _clean_text(anchor.get_text(" ", strip=True), limit=700),
                "list_video_files": files,
                "embedded": bool(files),
            }
        )
    return records


def extract_luce_declared_pages(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"\bpagina\s+\d+.*?\bdi\s+([\d\s.,]+)", text, flags=re.IGNORECASE)
    if not match:
        match = re.search(r"\bdi\s+([\d\s.,]+)", text, flags=re.IGNORECASE)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def parse_luce_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    raw_text = _clean_text(soup.get_text(" ", strip=True))
    title = _meta_content(soup, "og:title")
    if not title and soup.title:
        title = re.sub(r"\s+-\s+Archivio storico Istituto Luce$", "", _clean_text(soup.title.get_text(" ", strip=True)))
    abstract = _meta_content(soup, "og:description")
    files = extract_luce_video_files(html_text)
    date_value = _extract_labeled_value(raw_text, "data")
    duration = _extract_labeled_value(raw_text, "durata")
    color = _extract_labeled_value(raw_text, "colore")
    sound = _extract_labeled_value(raw_text, "sonoro")
    film_code = _extract_labeled_value(raw_text, "codice filmato")
    director = _extract_labeled_value(raw_text, "regia di")
    language = _extract_labeled_value(raw_text, "edizione lingua")
    nationality = _extract_labeled_value(raw_text, "nazionalità")
    producer = _extract_labeled_value(raw_text, "Casa di produzione")
    sequences = _extract_section(raw_text, "sequenze", ["keywords", "torna alla ricerca", "aggiungi ai preferiti"])
    keywords = _extract_section(raw_text, "keywords", ["aggiungi ai preferiti", "condividi", "copia il link", "Top"])
    subject = _clean_text(
        " | ".join(value for value in [keywords, nationality, producer, director] if value),
        limit=700,
    )
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública do catálogo cinematográfico Archivio Luce.",
                f"código: {film_code}" if film_code else "",
                f"duração: {duration}" if duration else "",
                f"cor: {color}" if color else "",
                f"som: {sound}" if sound else "",
                f"direção: {director}" if director else "",
                f"língua: {language}" if language else "",
                f"nacionalidade: {nationality}" if nationality else "",
                f"produção: {producer}" if producer else "",
                f"mídia pública detectada: {len(files)} arquivo(s)" if files else "registro descritivo sem arquivo HLS/MP4 exposto na ficha",
                abstract,
                sequences,
            ]
            if value
        ),
        limit=1600,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "source_kind": "luce_cinematic_archive_record",
        "video_link": _preferred_video_link(files, page_url),
        "page_url": page_url,
        "platform": LUCE_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": _extract_year(date_value),
        "embedded": bool(files),
        "video_files": files,
    }


def _collect_search_records(institution, internal_pages, errors):
    records_by_id = {}
    declared_pages = 0
    for page_index in range(LUCE_MAX_RESULT_PAGES):
        start = page_index * 20
        page_url = LUCE_CATALOG_FILMS_PAGE_URL_TEMPLATE.format(start=start)
        try:
            response = _fetch(page_url)
            response.raise_for_status()
            page_records = parse_luce_search_page(response.text, response.url)
            declared_pages = max(declared_pages, extract_luce_declared_pages(response.text))
            for record in page_records:
                records_by_id.setdefault(record["record_id"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    sum(1 for record in page_records if record.get("embedded")),
                    f"Página {page_index + 1} do recorte público `Archivio cinematografico` no catálogo Luce.",
                )
            )
        except Exception as error:
            errors.append(f"{page_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "erro",
                    warning="Falha ao abrir página de resultados do catálogo cinematográfico Luce.",
                    error=str(error),
                )
            )
        time.sleep(LUCE_REQUEST_PAUSE)
    return records_by_id, declared_pages


def _fetch_detail(listed_record):
    try:
        response = _fetch(listed_record["page_url"])
        response.raise_for_status()
        parsed = parse_luce_detail_page(response.text, response.url)
        return listed_record["record_id"], {**listed_record, **parsed}, response.status_code, ""
    except Exception as error:
        return listed_record["record_id"], listed_record, "", str(error)


def collect_luce_dataset():
    institutions = collect_luce_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    for url, warning in [
        (LUCE_HOME_URL, "Site oficial do Archivio Storico Istituto Luce."),
        (LUCE_CINEMATIC_ARCHIVE_URL, "Página oficial do Archivio cinematografico e link para `Vedi tutti i filmati`."),
        (LUCE_CINECITTA_ARCHIVE_URL, "Página institucional Cinecittà sobre o arquivo histórico."),
        (LUCE_CATALOG_HOME_URL, "Aplicação pública do catálogo `patrimonio.archivioluce.com/luce-web`."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    listed_records, declared_pages = _collect_search_records(institution, internal_pages, errors)
    records = []
    with ThreadPoolExecutor(max_workers=LUCE_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, record) for record in listed_records.values()]
        for future in as_completed(futures):
            record_id, record, status_code, error = future.result()
            if error:
                errors.append(f"{record.get('page_url', record_id)}: {error}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        record.get("page_url", record_id),
                        "erro",
                        warning="Falha ao abrir ficha pública do catálogo Luce.",
                        error=error,
                    )
                )
                continue
            records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    record["page_url"],
                    "ok",
                    status_code,
                    1,
                    1 if record.get("embedded") else 0,
                    "Ficha pública do catálogo cinematográfico Luce verificada.",
                )
            )

    records = sorted(records, key=lambda record: (record.get("date", ""), record.get("title", "")))
    video_links = [_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": LUCE_CATALOG_FILMS_URL,
            "partner_domain": normalize_domain(LUCE_CATALOG_FILMS_URL),
            "status": "ok" if records else "erro",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "instavel",
            "final_url": LUCE_CATALOG_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte público `Archivio cinematografico` do Archivio Luce. "
                f"O catálogo indica {declared_pages or 'múltiplas'} páginas de resultados; o MVP materializa "
                f"{len(records)} fichas em até {LUCE_MAX_RESULT_PAGES} páginas de listagem, sem baixar mídia "
                "e sem afirmar exaustividade do acervo Luce.",
                limit=1200,
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "LUCE_ARCHIVE_TYPE",
    "LUCE_COUNTRY",
    "LUCE_DETAIL_WORKERS",
    "LUCE_INSTITUTION_NAME",
    "LUCE_MAX_RESULT_PAGES",
    "LUCE_PLATFORM_LABEL",
    "LUCE_REPOSITORY_CODE",
    "collect_luce_dataset",
    "collect_luce_institutions",
    "extract_luce_declared_pages",
    "extract_luce_video_files",
    "parse_luce_detail_page",
    "parse_luce_search_page",
]
