import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CINEMATHEQUE_BRETAGNE_FILMS_PAGE_URL_TEMPLATE,
    CINEMATHEQUE_BRETAGNE_FILMS_URL,
    CINEMATHEQUE_BRETAGNE_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMATHEQUE_BRETAGNE_REPOSITORY_CODE = "FR-CINEMATHEQUE-BRETAGNE"
CINEMATHEQUE_BRETAGNE_ARCHIVE_TYPE = "Regional audiovisual and amateur film archive"
CINEMATHEQUE_BRETAGNE_COUNTRY = normalize_country("France")
CINEMATHEQUE_BRETAGNE_INSTITUTION_NAME = "Cinémathèque de Bretagne"
CINEMATHEQUE_BRETAGNE_PLATFORM_LABEL = "Cinémathèque de Bretagne"
CINEMATHEQUE_BRETAGNE_MAX_LIST_PAGES = 2
CINEMATHEQUE_BRETAGNE_MAX_DETAIL_PAGES = 20
CINEMATHEQUE_BRETAGNE_DETAIL_WORKERS = 4

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = None
    for attempt in range(4):
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        if response.status_code not in {429, 503}:
            return response
        time.sleep(1.2 * (attempt + 1))
    return response


def _extract_record_id(url):
    match = re.search(r"-426-(\d+)-0-\d+\.html", str(url or ""))
    return match.group(1) if match else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _list_url(page):
    if page <= 1:
        return CINEMATHEQUE_BRETAGNE_FILMS_URL
    return CINEMATHEQUE_BRETAGNE_FILMS_PAGE_URL_TEMPLATE.format(page=page)


def collect_cinematheque_bretagne_institutions():
    return [
        {
            "institution": CINEMATHEQUE_BRETAGNE_INSTITUTION_NAME,
            "slug": slugify(CINEMATHEQUE_BRETAGNE_INSTITUTION_NAME),
            "country": CINEMATHEQUE_BRETAGNE_COUNTRY,
            "continent": country_to_continent(CINEMATHEQUE_BRETAGNE_COUNTRY),
            "repository_code": CINEMATHEQUE_BRETAGNE_REPOSITORY_CODE,
            "archive_type": CINEMATHEQUE_BRETAGNE_ARCHIVE_TYPE,
            "cinematheque_bretagne_detail_url": CINEMATHEQUE_BRETAGNE_HOME_URL,
            "external_url": CINEMATHEQUE_BRETAGNE_FILMS_URL,
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
        "repository_code": CINEMATHEQUE_BRETAGNE_REPOSITORY_CODE,
        "archive_type": CINEMATHEQUE_BRETAGNE_ARCHIVE_TYPE,
        "cinematheque_bretagne_detail_url": CINEMATHEQUE_BRETAGNE_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMATHEQUE_BRETAGNE_FILMS_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cinematheque_bretagne_list_page(html_text, page_url=CINEMATHEQUE_BRETAGNE_FILMS_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    anchors = soup.find_all(
        "a",
        href=re.compile(r"voir-les-films-.+-426-\d+-0-\d+\.html\??", re.I),
    )
    for anchor in anchors:
        detail_url = urljoin(page_url, anchor.get("href", "").rstrip("?"))
        record_id = _extract_record_id(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        item = anchor.find_parent("li", class_=re.compile(r"nouvelleCont")) or anchor.find_parent("li")
        title = _clean_text(anchor.get("title") or anchor.get_text(" ", strip=True))
        meta = _clean_text((item.select_one(".reaAnnee h3") or item).get_text(" ", strip=True))
        category = _clean_text((item.select_one(".PABret") or "").get_text(" ", strip=True))
        resume = _clean_text((item.select_one(".Resume") or "").get_text(" ", strip=True), limit=700)
        creator = ""
        if "|" in meta:
            creator = _clean_text(" | ".join(part.strip() for part in meta.split("|")[1:] if part.strip()))
        year = _extract_year(meta)
        description = _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública da Cinémathèque de Bretagne; registro materializado a partir da listagem oficial.",
                    f"realização: {creator}" if creator else "",
                    f"categoria: {category}" if category else "",
                    resume,
                ]
                if value
            ),
            limit=1000,
        )
        records.append(
            {
                "record_id": record_id,
                "source_kind": "cinematheque_bretagne_listing_record",
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": CINEMATHEQUE_BRETAGNE_PLATFORM_LABEL,
                "title": title,
                "subject": "; ".join(value for value in [creator, category] if value),
                "description": description,
                "date": year,
                "embedded": False,
            }
        )
    return records


def extract_cinematheque_bretagne_declared_free_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"([\d\s]+)\s+Films\s+en\s+accès\s+libre", text, re.I)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_cinematheque_bretagne_declared_list_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"\[\s*\d+\s*-\s*\d+\s*/\s*([\d\s]+)\s*\]", text)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_cinematheque_bretagne_declared_pages(html_text):
    pages = [int(page) for page in re.findall(r"voir-les-films-426-0-0-(\d+)\.html", html_text or "")]
    return max(pages) if pages else 1


def _extract_title(soup):
    title_block = soup.select_one(".ficheTitle h2") or soup.select_one(".ficheTitle") or soup.find("title")
    title = _clean_text(title_block.get_text(" ", strip=True) if title_block else "", limit=250)
    title = re.sub(r"\s+-\s+Voir les films.*$", "", title).strip()
    return re.sub(r"\s{2,}", " ", title)


def _extract_detail_metadata(soup):
    metadata = {}
    for item in soup.select(".mainCd li"):
        values = [_clean_text(value) for value in item.stripped_strings if _clean_text(value)]
        if len(values) >= 2:
            metadata[values[0].lower()] = _clean_text(" ".join(values[1:]), limit=700)
    return metadata


def _metadata_value(metadata, *keys):
    for key in keys:
        value = metadata.get(key.lower(), "")
        if value:
            return value
    return ""


def _extract_section_text(soup, section_id):
    section = soup.select_one(section_id)
    if not section:
        return ""
    return _clean_text(section.get_text(" ", strip=True), limit=1200)


def parse_cinematheque_bretagne_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title = _extract_title(soup)
    metadata = _extract_detail_metadata(soup)
    category = _clean_text((soup.select_one(".PABret") or "").get_text(" ", strip=True))
    iframe = soup.find("iframe", src=re.compile(r"diazcdb\.oembed\.diazinteregio\.org/embed/", re.I))
    embed_url = iframe.get("src", "") if iframe else ""
    creator_block = soup.select_one(".ficheTitle h2")
    creator = _clean_text(creator_block.get_text(" ", strip=True) if creator_block else "", limit=500)
    if title and creator.startswith(title):
        creator = creator[len(title) :].strip(" -|")
    year = _extract_year(soup.get_text(" ", strip=True))
    resume = _extract_section_text(soup, "#section_resume")
    sequences = _extract_section_text(soup, "#section_sequences")
    subject = "; ".join(value for value in [creator, category] if value)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública da Cinémathèque de Bretagne.",
                f"duração: {_metadata_value(metadata, 'durée', 'duree')}" if _metadata_value(metadata, "durée", "duree") else "",
                f"formato original: {_metadata_value(metadata, 'format original')}" if _metadata_value(metadata, "format original") else "",
                f"som: {_metadata_value(metadata, 'son')}" if _metadata_value(metadata, "son") else "",
                f"coloração: {_metadata_value(metadata, 'coloration')}" if _metadata_value(metadata, "coloration") else "",
                f"categoria: {category}" if category else "",
                f"embed: {embed_url}" if embed_url else "registro descritivo sem iframe público detectado na ficha",
                resume,
                sequences,
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "source_kind": "cinematheque_bretagne_detail_record",
        "page_url": page_url,
        "video_link": embed_url or page_url,
        "platform": CINEMATHEQUE_BRETAGNE_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": year,
        "embedded": bool(embed_url),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CINEMATHEQUE_BRETAGNE_FILMS_URL,
        "platform": CINEMATHEQUE_BRETAGNE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record):
    response = _fetch(record["page_url"])
    response.raise_for_status()
    return parse_cinematheque_bretagne_detail_page(response.text, response.url), response.url, response.status_code


def collect_cinematheque_bretagne_dataset():
    institutions = collect_cinematheque_bretagne_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_free_total = 0
    declared_list_total = 0
    declared_pages = 0

    for url, warning in [
        (CINEMATHEQUE_BRETAGNE_HOME_URL, "Site institucional da Cinémathèque de Bretagne."),
        (CINEMATHEQUE_BRETAGNE_FILMS_URL, "Rota pública `Voir les films`; rota principal de coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
            declared_free_total = max(declared_free_total, extract_cinematheque_bretagne_declared_free_total(response.text))
            declared_list_total = max(declared_list_total, extract_cinematheque_bretagne_declared_list_total(response.text))
            declared_pages = max(declared_pages, extract_cinematheque_bretagne_declared_pages(response.text))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CINEMATHEQUE_BRETAGNE_MAX_LIST_PAGES + 1):
        list_url = _list_url(page)
        try:
            response = _fetch(list_url)
            response.raise_for_status()
            page_records = parse_cinematheque_bretagne_list_page(response.text, response.url)
            declared_free_total = max(declared_free_total, extract_cinematheque_bretagne_declared_free_total(response.text))
            declared_list_total = max(declared_list_total, extract_cinematheque_bretagne_declared_list_total(response.text))
            declared_pages = max(declared_pages, extract_cinematheque_bretagne_declared_pages(response.text))
            for record in page_records:
                records_by_id[record["record_id"]] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    0,
                    f"Página {page} da listagem pública `Voir les films` da Cinémathèque de Bretagne.",
                )
            )
        except Exception as error:
            errors.append(f"{list_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    list_url,
                    "erro",
                    warning="Falha ao abrir listagem pública da Cinémathèque de Bretagne.",
                    error=str(error),
                )
            )

    detail_records = list(records_by_id.values())[:CINEMATHEQUE_BRETAGNE_MAX_DETAIL_PAGES]
    with ThreadPoolExecutor(max_workers=CINEMATHEQUE_BRETAGNE_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, record) for record in detail_records]
        for future in as_completed(futures):
            try:
                parsed, final_url, http_code = future.result()
                if parsed["record_id"] in records_by_id:
                    list_title = records_by_id[parsed["record_id"]].get("title", "")
                    records_by_id[parsed["record_id"]].update(parsed)
                    if list_title:
                        records_by_id[parsed["record_id"]]["title"] = list_title
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        final_url,
                        "ok",
                        http_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública aberta para metadados e iframe Diaz/OEmbed.",
                    )
                )
            except Exception as error:
                errors.append(str(error))
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        CINEMATHEQUE_BRETAGNE_FILMS_URL,
                        "erro",
                        warning="Falha ao abrir ficha pública da Cinémathèque de Bretagne.",
                        error=str(error),
                    )
                )

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEMATHEQUE_BRETAGNE_FILMS_URL,
            "partner_domain": normalize_domain(CINEMATHEQUE_BRETAGNE_FILMS_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CINEMATHEQUE_BRETAGNE_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte público `Voir les films` da Cinémathèque de Bretagne. "
                f"O site declara {declared_free_total or 'milhares de'} filmes em acesso livre; "
                f"a listagem pública indica {declared_list_total or 'múltiplos'} registros/resultados em até "
                f"{declared_pages or 'múltiplas'} páginas visíveis. O MVP materializa {len(records)} fichas "
                f"em até {CINEMATHEQUE_BRETAGNE_MAX_LIST_PAGES} páginas e enriquece até "
                f"{CINEMATHEQUE_BRETAGNE_MAX_DETAIL_PAGES} fichas detalhadas, sem baixar mídia e sem afirmar "
                "cobertura total do acervo preservado."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMATHEQUE_BRETAGNE_ARCHIVE_TYPE",
    "CINEMATHEQUE_BRETAGNE_COUNTRY",
    "CINEMATHEQUE_BRETAGNE_INSTITUTION_NAME",
    "CINEMATHEQUE_BRETAGNE_MAX_DETAIL_PAGES",
    "CINEMATHEQUE_BRETAGNE_MAX_LIST_PAGES",
    "CINEMATHEQUE_BRETAGNE_PLATFORM_LABEL",
    "CINEMATHEQUE_BRETAGNE_REPOSITORY_CODE",
    "collect_cinematheque_bretagne_dataset",
    "collect_cinematheque_bretagne_institutions",
    "extract_cinematheque_bretagne_declared_free_total",
    "extract_cinematheque_bretagne_declared_list_total",
    "extract_cinematheque_bretagne_declared_pages",
    "parse_cinematheque_bretagne_detail_page",
    "parse_cinematheque_bretagne_list_page",
]
