import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import CPSA_FILMS_PAGE_URL_TEMPLATE, CPSA_FILMS_URL, CPSA_HOME_URL, HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CPSA_REPOSITORY_CODE = "FR-CPSA"
CPSA_ARCHIVE_TYPE = "Regional audiovisual and amateur film archive"
CPSA_COUNTRY = normalize_country("France")
CPSA_INSTITUTION_NAME = "Cinémathèque des Pays de Savoie et de l'Ain"
CPSA_PLATFORM_LABEL = "Cinémathèque des Pays de Savoie et de l'Ain"
CPSA_MAX_LIST_PAGES = 2
CPSA_MAX_DETAIL_PAGES = 20
CPSA_DETAIL_WORKERS = 4

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
    match = re.search(r"-527-(\d+)-0-\d+\.html", str(url or ""))
    return match.group(1) if match else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _list_url(page):
    if page <= 1:
        return CPSA_FILMS_URL
    return CPSA_FILMS_PAGE_URL_TEMPLATE.format(page=page)


def collect_cpsa_institutions():
    return [
        {
            "institution": CPSA_INSTITUTION_NAME,
            "slug": slugify(CPSA_INSTITUTION_NAME),
            "country": CPSA_COUNTRY,
            "continent": country_to_continent(CPSA_COUNTRY),
            "repository_code": CPSA_REPOSITORY_CODE,
            "archive_type": CPSA_ARCHIVE_TYPE,
            "cpsa_detail_url": CPSA_HOME_URL,
            "external_url": CPSA_FILMS_URL,
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
        "repository_code": CPSA_REPOSITORY_CODE,
        "archive_type": CPSA_ARCHIVE_TYPE,
        "cpsa_detail_url": CPSA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CPSA_FILMS_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cpsa_list_page(html_text, page_url=CPSA_FILMS_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    anchors = soup.find_all(
        "a",
        href=re.compile(r"-527-\d+-0-\d+\.html\??", re.I),
    )
    for anchor in anchors:
        detail_url = urljoin(page_url, anchor.get("href", "").rstrip("?"))
        record_id = _extract_record_id(detail_url)
        if not record_id or record_id == "0" or record_id in seen:
            continue
        seen.add(record_id)
        item = anchor.find_parent("li", class_=re.compile(r"nouvelleCont")) or anchor.find_parent("li")
        title = _clean_text(anchor.get("title") or anchor.get_text(" ", strip=True))
        meta = _clean_text((item or anchor).get_text(" ", strip=True))
        year = _extract_year(meta)
        creator = ""
        if title and meta:
            creator = _clean_text(meta.replace(title, "").replace(year, ""), limit=250)
        records.append(
            {
                "record_id": record_id,
                "source_kind": "cpsa_listing_record",
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": CPSA_PLATFORM_LABEL,
                "title": title,
                "subject": creator,
                "description": _clean_text(
                    "Ficha pública da Cinémathèque des Pays de Savoie et de l'Ain; "
                    "registro materializado a partir da listagem oficial.",
                    limit=1000,
                ),
                "date": year,
                "embedded": False,
            }
        )
    return records


def extract_cpsa_declared_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"([\d\s]+)\s+film\(s\)", text, re.I)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_cpsa_declared_pages(html_text):
    pages = [int(page) for page in re.findall(r"le-catalogue-des-collections-527-0-0-(\d+)\.html", html_text or "")]
    return max(pages) if pages else 1


def _extract_title(soup):
    heading = soup.find(["h1", "h2"])
    title = _clean_text(heading.get_text(" ", strip=True) if heading else soup.title.get_text(" ", strip=True), limit=250)
    return re.sub(r"\s+-\s+Le Catalogue.*$", "", title).strip()


def _metadata_value(text, label):
    labels = [
        "Synopsis",
        "Réalisation",
        "Date",
        "Lieu(x)",
        "Descripteurs",
        "Format",
        "Coloration",
        "Son",
        "Durée",
        "Support(s)",
    ]
    start_match = re.search(rf"{re.escape(label)}\s*:", text, re.I)
    if not start_match:
        return ""
    start = start_match.end()
    next_positions = [
        match.start()
        for candidate in labels
        if candidate.lower() != label.lower()
        for match in [re.search(rf"\s{re.escape(candidate)}\s*:", text[start:], re.I)]
        if match
    ]
    end = start + min(next_positions) if next_positions else len(text)
    return _clean_text(text[start:end], limit=400)


def _extract_embed_url(html_text):
    match = re.search(r"https?://diazcpsa\.oembed\.diazinteregio\.org/embed/[^\"'\s<>]+", html_text or "", re.I)
    return match.group(0) if match else ""


def parse_cpsa_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True), limit=5000)
    title = _extract_title(soup)
    embed_url = _extract_embed_url(html_text)
    synopsis = _metadata_value(text, "Synopsis")
    creator = _metadata_value(text, "Réalisation")
    place = _metadata_value(text, "Lieu(x)")
    descriptors = _metadata_value(text, "Descripteurs")
    duration = _metadata_value(text, "Durée")
    original_format = _metadata_value(text, "Format")
    sound = _metadata_value(text, "Son")
    coloration = _metadata_value(text, "Coloration")
    year = _extract_year(_metadata_value(text, "Date") or text)
    subject = "; ".join(value for value in [creator, place, descriptors] if value)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública da Cinémathèque des Pays de Savoie et de l'Ain.",
                f"duração: {duration}" if duration else "",
                f"formato: {original_format}" if original_format else "",
                f"som: {sound}" if sound else "",
                f"coloração: {coloration}" if coloration else "",
                f"embed: {embed_url}" if embed_url else "registro descritivo sem OEmbed público detectado na ficha",
                synopsis,
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "source_kind": "cpsa_detail_record",
        "page_url": page_url,
        "video_link": embed_url or page_url,
        "platform": CPSA_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": year,
        "embedded": bool(embed_url),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CPSA_FILMS_URL,
        "platform": CPSA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record):
    response = _fetch(record["page_url"])
    response.raise_for_status()
    return parse_cpsa_detail_page(response.text, response.url), response.url, response.status_code


def collect_cpsa_dataset():
    institutions = collect_cpsa_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_total = 0
    declared_pages = 0

    for url, warning in [
        (CPSA_HOME_URL, "Site institucional da Cinémathèque des Pays de Savoie et de l'Ain."),
        (CPSA_FILMS_URL, "Rota pública `Le Catalogue des Collections`; rota principal de coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
            declared_total = max(declared_total, extract_cpsa_declared_total(response.text))
            declared_pages = max(declared_pages, extract_cpsa_declared_pages(response.text))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CPSA_MAX_LIST_PAGES + 1):
        list_url = _list_url(page)
        try:
            response = _fetch(list_url)
            response.raise_for_status()
            page_records = parse_cpsa_list_page(response.text, response.url)
            declared_total = max(declared_total, extract_cpsa_declared_total(response.text))
            declared_pages = max(declared_pages, extract_cpsa_declared_pages(response.text))
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
                    f"Página {page} da listagem pública do catálogo da CPSA.",
                )
            )
        except Exception as error:
            errors.append(f"{list_url}: {error}")
            internal_pages.append(
                _internal_page_row(institution, list_url, "erro", warning="Falha ao abrir listagem pública da CPSA.", error=str(error))
            )

    with ThreadPoolExecutor(max_workers=CPSA_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, record) for record in list(records_by_id.values())[:CPSA_MAX_DETAIL_PAGES]]
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
                        "Ficha pública aberta para metadados e OEmbed Diaz/CPSA.",
                    )
                )
            except Exception as error:
                errors.append(str(error))

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": CPSA_FILMS_URL,
            "partner_domain": normalize_domain(CPSA_FILMS_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CPSA_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte público `Le Catalogue des Collections` da Cinémathèque des Pays de "
                f"Savoie et de l'Ain. O site declara {declared_total or 'múltiplos'} filmes em "
                f"{declared_pages or 'múltiplas'} páginas. O MVP materializa {len(records)} fichas em até "
                f"{CPSA_MAX_LIST_PAGES} páginas e enriquece até {CPSA_MAX_DETAIL_PAGES} fichas detalhadas, "
                "sem baixar mídia e sem afirmar cobertura total do acervo preservado."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CPSA_ARCHIVE_TYPE",
    "CPSA_COUNTRY",
    "CPSA_INSTITUTION_NAME",
    "CPSA_MAX_DETAIL_PAGES",
    "CPSA_MAX_LIST_PAGES",
    "CPSA_PLATFORM_LABEL",
    "CPSA_REPOSITORY_CODE",
    "collect_cpsa_dataset",
    "collect_cpsa_institutions",
    "extract_cpsa_declared_pages",
    "extract_cpsa_declared_total",
    "parse_cpsa_detail_page",
    "parse_cpsa_list_page",
]
