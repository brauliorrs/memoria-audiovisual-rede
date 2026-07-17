import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CINEARCHIVES_CATALOG_PAGE_URL_TEMPLATE,
    CINEARCHIVES_CATALOG_URL,
    CINEARCHIVES_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEARCHIVES_REPOSITORY_CODE = "FR-CINEARCHIVES"
CINEARCHIVES_ARCHIVE_TYPE = "Institutional film and labour movement audiovisual archive"
CINEARCHIVES_COUNTRY = normalize_country("France")
CINEARCHIVES_INSTITUTION_NAME = "Ciné-Archives"
CINEARCHIVES_PLATFORM_LABEL = "Ciné-Archives"
CINEARCHIVES_MAX_LIST_PAGES = 2
CINEARCHIVES_MAX_DETAIL_PAGES = 20
CINEARCHIVES_DETAIL_WORKERS = 4
CINEARCHIVES_REQUEST_PAUSE = 0.12

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
    match = re.search(r"-1104-(\d+)-1-\d+\.html", str(url or ""))
    return match.group(1) if match else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _list_url(page):
    if page <= 1:
        return CINEARCHIVES_CATALOG_URL
    return CINEARCHIVES_CATALOG_PAGE_URL_TEMPLATE.format(page=page)


def collect_cinearchives_institutions():
    return [
        {
            "institution": CINEARCHIVES_INSTITUTION_NAME,
            "slug": slugify(CINEARCHIVES_INSTITUTION_NAME),
            "country": CINEARCHIVES_COUNTRY,
            "continent": country_to_continent(CINEARCHIVES_COUNTRY),
            "repository_code": CINEARCHIVES_REPOSITORY_CODE,
            "archive_type": CINEARCHIVES_ARCHIVE_TYPE,
            "cinearchives_detail_url": CINEARCHIVES_HOME_URL,
            "external_url": CINEARCHIVES_CATALOG_URL,
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
        "repository_code": CINEARCHIVES_REPOSITORY_CODE,
        "archive_type": CINEARCHIVES_ARCHIVE_TYPE,
        "cinearchives_detail_url": CINEARCHIVES_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEARCHIVES_CATALOG_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cinearchives_list_page(html_text, page_url=CINEARCHIVES_CATALOG_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for item in soup.select("article.diaListItem"):
        anchor = item.find("a", href=re.compile(r"catalogue-.+-1104-\d+-1-\d+\.html"))
        if not anchor:
            continue
        detail_url = urljoin(page_url, anchor.get("href", ""))
        record_id = _extract_record_id(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        lines = [_clean_text(line) for line in item.get_text("\n", strip=True).split("\n") if _clean_text(line)]
        title = _clean_text(anchor.get_text(" ", strip=True))
        meta_parts = [_clean_text(part) for part in (lines[1].split("|") if len(lines) > 1 else [])]
        meta_parts = [part for part in meta_parts if part]
        year = _extract_year(meta_parts[0] if meta_parts else " ".join(lines[1:3]))
        creator = meta_parts[1] if len(meta_parts) > 1 else ""
        duration = next((part for part in meta_parts if re.match(r"\d{2}:\d{2}:\d{2}", part)), "")
        sound = next((part for part in meta_parts if part in {"Muet", "Sonore", "Son manquant"}), "")
        teaser = " ".join(line for line in lines[2:] if line.strip(". "))
        description = _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública do catálogo Ciné-Archives; registro materializado a partir da listagem oficial.",
                    f"realização: {creator}" if creator else "",
                    f"duração: {duration}" if duration else "",
                    f"som: {sound}" if sound else "",
                    teaser,
                ]
                if value
            ),
            limit=1000,
        )
        records.append(
            {
                "record_id": record_id,
                "source_kind": "cinearchives_listing_record",
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": CINEARCHIVES_PLATFORM_LABEL,
                "title": title,
                "subject": "; ".join(value for value in [creator, sound] if value),
                "description": description,
                "date": year,
                "embedded": False,
            }
        )
    return records


def extract_cinearchives_declared_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"([\d\s]+)\s+résultat\(s\)", text)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_cinearchives_declared_pages(html_text):
    pages = [int(page) for page in re.findall(r"catalogue-1104-0-0-(\d+)\.html", html_text or "")]
    return max(pages) if pages else 1


def _parse_meta_items(soup):
    metadata = {}
    for item in soup.select("li.val"):
        lines = [_clean_text(value) for value in item.stripped_strings if _clean_text(value)]
        if len(lines) >= 2:
            metadata[lines[0].lower()] = _clean_text(" ".join(lines[1:]), limit=700)
    return metadata


def _metadata_value(metadata, *keys):
    for key in keys:
        value = metadata.get(key.lower(), "")
        if value:
            return value
    return ""


def _extract_keywords(soup):
    values = []
    for block in soup.select(".diaKeywords"):
        text = _clean_text(block.get_text(" | ", strip=True), limit=700)
        if text:
            values.append(text)
    return " | ".join(values)


def _extract_description(soup):
    main = soup.select_one(".diaMain")
    if not main:
        return ""
    text = main.get_text(" ", strip=True)
    for marker in ["D'autres films peuvent vous intéresser", "Ici les suggestions"]:
        text = text.split(marker, 1)[0]
    return _clean_text(text, limit=1400)


def parse_cinearchives_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title = _clean_text((soup.find("h1") or soup).get_text(" ", strip=True), limit=250)
    metadata = _parse_meta_items(soup)
    keywords = _extract_keywords(soup)
    description_text = _extract_description(soup)
    iframe = soup.find("iframe", src=re.compile(r"diazcinearchives\.oembed\.diazinteregio\.org/embed/", re.I))
    embed_url = iframe.get("src", "") if iframe else ""
    year = _extract_year(_metadata_value(metadata, "année(s)", "annee(s)"))
    subject = "; ".join(
        value
        for value in [
            _metadata_value(metadata, "réalisateur.ice.s", "realisateur.ice.s"),
            _metadata_value(metadata, "lieu(x)"),
            keywords,
        ]
        if value
    )
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública do catálogo Ciné-Archives.",
                f"ano: {_metadata_value(metadata, 'année(s)', 'annee(s)')}" if _metadata_value(metadata, "année(s)", "annee(s)") else "",
                f"duração: {_metadata_value(metadata, 'durée', 'duree')}" if _metadata_value(metadata, "durée", "duree") else "",
                f"formato: {_metadata_value(metadata, 'format')}" if _metadata_value(metadata, "format") else "",
                f"som: {_metadata_value(metadata, 'son')}" if _metadata_value(metadata, "son") else "",
                f"coloração: {_metadata_value(metadata, 'coloration')}" if _metadata_value(metadata, "coloration") else "",
                f"coleção: {_metadata_value(metadata, 'collection')}" if _metadata_value(metadata, "collection") else "",
                f"embed: {embed_url}" if embed_url else "registro descritivo sem iframe público detectado na ficha",
                description_text,
            ]
            if value
        ),
        limit=1600,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "source_kind": "cinearchives_detail_record",
        "page_url": page_url,
        "video_link": embed_url or page_url,
        "platform": CINEARCHIVES_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": year,
        "embedded": bool(embed_url),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CINEARCHIVES_CATALOG_URL,
        "platform": CINEARCHIVES_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record):
    response = _fetch(record["page_url"])
    response.raise_for_status()
    return parse_cinearchives_detail_page(response.text, response.url), response.url, response.status_code


def collect_cinearchives_dataset():
    institutions = collect_cinearchives_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_total = 0
    declared_pages = 0

    for url, warning in [
        (CINEARCHIVES_HOME_URL, "Site institucional Ciné-Archives."),
        (CINEARCHIVES_CATALOG_URL, "Catálogo completo com mais de 900 filmes em linha; rota principal de coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
            declared_total = max(declared_total, extract_cinearchives_declared_total(response.text))
            declared_pages = max(declared_pages, extract_cinearchives_declared_pages(response.text))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CINEARCHIVES_MAX_LIST_PAGES + 1):
        list_url = _list_url(page)
        try:
            response = _fetch(list_url)
            response.raise_for_status()
            page_records = parse_cinearchives_list_page(response.text, response.url)
            declared_total = max(declared_total, extract_cinearchives_declared_total(response.text))
            declared_pages = max(declared_pages, extract_cinearchives_declared_pages(response.text))
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
                    f"Página {page} da listagem pública do catálogo Ciné-Archives.",
                )
            )
        except Exception as error:
            errors.append(f"{list_url}: {error}")
            internal_pages.append(_internal_page_row(institution, list_url, "erro", warning="Falha ao abrir listagem pública Ciné-Archives.", error=str(error)))

    detail_records = list(records_by_id.values())[:CINEARCHIVES_MAX_DETAIL_PAGES]
    with ThreadPoolExecutor(max_workers=CINEARCHIVES_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, record) for record in detail_records]
        for future in as_completed(futures):
            try:
                parsed, final_url, http_code = future.result()
                if parsed["record_id"] in records_by_id:
                    records_by_id[parsed["record_id"]].update(parsed)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        final_url,
                        "ok",
                        http_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública Ciné-Archives aberta para metadados e iframe Diaz.",
                    )
                )
            except Exception as error:
                errors.append(str(error))
                internal_pages.append(_internal_page_row(institution, CINEARCHIVES_CATALOG_URL, "erro", warning="Falha ao abrir ficha pública Ciné-Archives.", error=str(error)))

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEARCHIVES_CATALOG_URL,
            "partner_domain": normalize_domain(CINEARCHIVES_CATALOG_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CINEARCHIVES_CATALOG_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte público do catálogo Ciné-Archives. "
                f"A listagem declara {declared_total or 'mais de 900'} resultados em até {declared_pages or 'múltiplas'} páginas; "
                f"o MVP materializa {len(records)} fichas em até {CINEARCHIVES_MAX_LIST_PAGES} páginas e enriquece "
                f"até {CINEARCHIVES_MAX_DETAIL_PAGES} fichas detalhadas, sem baixar mídia e sem afirmar catálogo total."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEARCHIVES_ARCHIVE_TYPE",
    "CINEARCHIVES_COUNTRY",
    "CINEARCHIVES_INSTITUTION_NAME",
    "CINEARCHIVES_MAX_DETAIL_PAGES",
    "CINEARCHIVES_MAX_LIST_PAGES",
    "CINEARCHIVES_PLATFORM_LABEL",
    "CINEARCHIVES_REPOSITORY_CODE",
    "collect_cinearchives_dataset",
    "collect_cinearchives_institutions",
    "extract_cinearchives_declared_pages",
    "extract_cinearchives_declared_total",
    "parse_cinearchives_detail_page",
    "parse_cinearchives_list_page",
]
