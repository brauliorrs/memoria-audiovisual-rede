import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT, SAINT_ETIENNE_COLLECTIONS_URL, SAINT_ETIENNE_HOME_URL
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


SAINT_ETIENNE_REPOSITORY_CODE = "FR-CINEMATHEQUE-SAINT-ETIENNE"
SAINT_ETIENNE_ARCHIVE_TYPE = "Municipal cinematheque and regional film archive"
SAINT_ETIENNE_COUNTRY = normalize_country("France")
SAINT_ETIENNE_INSTITUTION_NAME = "Cinémathèque de Saint-Étienne"
SAINT_ETIENNE_PLATFORM_LABEL = "Cinémathèque de Saint-Étienne"
SAINT_ETIENNE_MAX_DETAIL_PAGES = 24
SAINT_ETIENNE_DETAIL_WORKERS = 4

SAINT_ETIENNE_SEED_DETAIL_URLS = [
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMjE2/une-capitale-industrielle-saint-etienne?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtNQ%3D%3D/adieu-chavanelle?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMjU1/mine-a-saint-jean-bonnefonds-la?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtNzM5/cine-journal-de-saint-etienne-1929?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMTQ2Ng%3D%3D/cine-journal-de-saint-etienne-1930?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMTkz/vivre-a-saint-etienne?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMTky/ville-a-soif-la?_lg=fr-FR",
    "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_b2FpLWNzZS5kaWF6aW50ZXJlZ2lvLm9yZy1kb2N1bWVudGFpcmUtMTE4/misere-silencieuse?_lg=fr-FR",
]

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


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _extract_identifier(text, page_url):
    match = re.search(r"IDENTIFIANT\s*:\s*([A-Za-z0-9_-]+)", text, re.I)
    if match:
        return match.group(1)
    url_match = re.search(r"/([^/?#]+)(?:\?_lg=fr-FR)?$", page_url)
    return url_match.group(1) if url_match else page_url


def _metadata_value(text, label):
    labels = [
        "FORMAT DE DUREE",
        "GENRE",
        "MOTS CLES",
        "PERIODE",
        "DATE DE REALISATION",
        "REALISATEUR",
        "PRODUCTEUR",
        "COLORATION",
        "SON",
        "DUREE",
        "IDENTIFIANT",
        "FORMAT ORIGINAL",
    ]
    start_match = re.search(rf"{re.escape(label)}\s*:\s*", text, re.I)
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
    return _clean_text(text[start:end], limit=700)


def collect_saint_etienne_institutions():
    return [
        {
            "institution": SAINT_ETIENNE_INSTITUTION_NAME,
            "slug": slugify(SAINT_ETIENNE_INSTITUTION_NAME),
            "country": SAINT_ETIENNE_COUNTRY,
            "continent": country_to_continent(SAINT_ETIENNE_COUNTRY),
            "repository_code": SAINT_ETIENNE_REPOSITORY_CODE,
            "archive_type": SAINT_ETIENNE_ARCHIVE_TYPE,
            "saint_etienne_detail_url": SAINT_ETIENNE_COLLECTIONS_URL,
            "external_url": SAINT_ETIENNE_HOME_URL,
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
        "repository_code": SAINT_ETIENNE_REPOSITORY_CODE,
        "archive_type": SAINT_ETIENNE_ARCHIVE_TYPE,
        "saint_etienne_detail_url": SAINT_ETIENNE_COLLECTIONS_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": SAINT_ETIENNE_HOME_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def extract_saint_etienne_detail_links(html_text, base_url=SAINT_ETIENNE_HOME_URL):
    links = []
    for match in re.finditer(r'href="([^"]*/Default/doc/OAI_1/[^"]+)"', html_text or "", re.I):
        links.append(urljoin(base_url, match.group(1).replace("&amp;", "&")))
    return list(dict.fromkeys(links))


def parse_saint_etienne_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = _clean_text(soup.get_text(" ", strip=True), limit=7000)
    og_title = soup.find("meta", attrs={"property": "og:title"}) or soup.find("meta", attrs={"name": "og:title"})
    title = _clean_text((og_title or {}).get("content", ""), limit=250)
    if not title:
        title = _clean_text((soup.find("title") or "").get_text(" ", strip=True), limit=250)
    title = re.sub(r"\s+-\s+Cinémathèque de Saint-?Etienne.*$", "", title).strip()
    synopsis = _metadata_value(text, "SYNOPSIS") or _clean_text(
        (soup.find("meta", attrs={"name": "description"}) or {}).get("content", ""),
        limit=900,
    )
    creators = _metadata_value(text, "REALISATEUR")
    producer = _metadata_value(text, "PRODUCTEUR")
    genre = _metadata_value(text, "GENRE")
    duration = _metadata_value(text, "DUREE")
    sound = _metadata_value(text, "SON")
    coloration = _metadata_value(text, "COLORATION")
    original_format = _metadata_value(text, "FORMAT ORIGINAL")
    date = _metadata_value(text, "DATE DE REALISATION")
    mp4_match = re.search(r"https?://diazcse\.oembed\.diazinteregio\.org/[^\"'\s<>]+\.mp4", html_text or "", re.I)
    video_link = mp4_match.group(0) if mp4_match else page_url
    return {
        "record_id": _extract_identifier(text, page_url),
        "source_kind": "saint_etienne_oai_detail_record",
        "page_url": page_url,
        "video_link": video_link,
        "platform": SAINT_ETIENNE_PLATFORM_LABEL,
        "title": title,
        "subject": _clean_text("; ".join(value for value in [creators, producer, genre] if value), limit=700),
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública OAI/Syracuse da Cinémathèque de Saint-Étienne.",
                    f"duração: {duration}" if duration else "",
                    f"som: {sound}" if sound else "",
                    f"coloração: {coloration}" if coloration else "",
                    f"formato original: {original_format}" if original_format else "",
                    f"mp4: {video_link}" if video_link.endswith(".mp4") else "registro sem MP4 público detectado na ficha",
                    synopsis,
                ]
                if value
            ),
            limit=1800,
        ),
        "date": _extract_year(date or text),
        "embedded": video_link.endswith(".mp4"),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": SAINT_ETIENNE_HOME_URL,
        "platform": SAINT_ETIENNE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(url):
    response = _fetch(url)
    response.raise_for_status()
    return parse_saint_etienne_detail_page(response.text, response.url), response.url, response.status_code, response.text


def collect_saint_etienne_dataset():
    institutions = collect_saint_etienne_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    candidate_urls = list(SAINT_ETIENNE_SEED_DETAIL_URLS)

    for url, warning in [
        (SAINT_ETIENNE_HOME_URL, "Site institucional da Cinémathèque de Saint-Étienne."),
        (SAINT_ETIENNE_COLLECTIONS_URL, "Página pública de coleções; declara seleção de filmes visíveis no site."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            candidate_urls.extend(extract_saint_etienne_detail_links(response.text, response.url))
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    with ThreadPoolExecutor(max_workers=SAINT_ETIENNE_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, url) for url in list(dict.fromkeys(candidate_urls))[:SAINT_ETIENNE_MAX_DETAIL_PAGES]]
        for future in as_completed(futures):
            try:
                parsed, final_url, http_code, html_text = future.result()
                records_by_id[parsed["record_id"]] = parsed
                candidate_urls.extend(extract_saint_etienne_detail_links(html_text, final_url))
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        final_url,
                        "ok",
                        http_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública OAI/Syracuse aberta para metadados e MP4 Diaz/CSE quando exposto.",
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
            "partner_site": SAINT_ETIENNE_HOME_URL,
            "partner_domain": normalize_domain(SAINT_ETIENNE_HOME_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": SAINT_ETIENNE_COLLECTIONS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado por fichas públicas OAI/Syracuse da Cinémathèque de Saint-Étienne. "
                f"O site declara 8.000 títulos catalogados, 6.000 arquivos digitalizados e seleção de filmes visíveis; "
                f"o MVP materializa {len(records)} fichas e detecta {embedded_total} MP4 públicos, sem baixar mídia "
                "e sem afirmar cobertura total do acervo preservado."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "SAINT_ETIENNE_ARCHIVE_TYPE",
    "SAINT_ETIENNE_COUNTRY",
    "SAINT_ETIENNE_INSTITUTION_NAME",
    "SAINT_ETIENNE_MAX_DETAIL_PAGES",
    "SAINT_ETIENNE_PLATFORM_LABEL",
    "SAINT_ETIENNE_REPOSITORY_CODE",
    "collect_saint_etienne_dataset",
    "collect_saint_etienne_institutions",
    "extract_saint_etienne_detail_links",
    "parse_saint_etienne_detail_page",
]
