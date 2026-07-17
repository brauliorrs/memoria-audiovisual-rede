from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
    DKULT_DUSSELDORF_AV_COLLECTION_URL,
    DKULT_DUSSELDORF_COLLECTION_PAGE_URL_TEMPLATE,
    FILMMUSEUM_DUSSELDORF_ARCHIVE_URL,
    FILMMUSEUM_DUSSELDORF_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FILMMUSEUM_DUSSELDORF_INSTITUTION_NAME = "Filmmuseum Düsseldorf"
FILMMUSEUM_DUSSELDORF_REPOSITORY_CODE = "DE-FILMMUSEUM-DUSSELDORF"
FILMMUSEUM_DUSSELDORF_ARCHIVE_TYPE = "Film museum archive with public metadata catalogue and restricted media access"
FILMMUSEUM_DUSSELDORF_COUNTRY = normalize_country("Germany")
FILMMUSEUM_DUSSELDORF_PLATFORM_LABEL = "d:kult online"
DKULT_DUSSELDORF_EXPECTED_AV_TOTAL = 300
DKULT_DUSSELDORF_MIN_AV_TOTAL = 300
DKULT_DUSSELDORF_DETAIL_WORKERS = 5

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "de,en;q=0.8,pt-BR;q=0.6",
        "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch_html(url, ajax=False):
    headers = dict(SESSION.headers)
    if ajax:
        headers.update({"X-Requested-With": "XMLHttpRequest", "X-Tapestry-Request": "true"})
    response = requests.get(url, headers=headers, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    return response.text, response.url, response.status_code


def _object_id_from_url(url):
    match = re.search(r"/objects/(\d+)/", str(url or ""))
    return match.group(1) if match else ""


def parse_dkult_object_links(html, page_url):
    soup = BeautifulSoup(html or "", "html.parser")
    links_by_url = {}
    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor["href"]).split("?")[0]
        if not re.search(r"/objects/\d+/", href):
            continue
        title = _clean_text(anchor.get_text(" ", strip=True))
        links_by_url.setdefault(href, title)
    return [{"object_id": _object_id_from_url(url), "object_url": url, "title_hint": title} for url, title in links_by_url.items()]


def _detail_fields(soup):
    fields = {}
    for field in soup.select(".detailField"):
        label_node = field.select_one(".detailFieldLabel") or field.select_one(".detail-category-label")
        if not label_node:
            continue
        label = _clean_text(label_node.get_text(" ", strip=True)).replace("  ", " ")
        value_nodes = field.select(".detailFieldValue") or field.select(".toggleContent")
        values = [_clean_text(node.get_text(" ", strip=True)) for node in value_nodes]
        values = [value for value in values if value and value != label]
        if values:
            fields.setdefault(label, []).extend(values)
    return fields


def _field_join(fields, label, *, limit=600):
    values = fields.get(label, [])
    return _clean_text("; ".join(dict.fromkeys(values)), limit=limit)


def parse_dkult_object_detail(html, object_url, title_hint=""):
    soup = BeautifulSoup(html or "", "html.parser")
    fields = _detail_fields(soup)
    title = _clean_text(soup.find("h1").get_text(" ", strip=True)) if soup.find("h1") else _clean_text(title_hint)
    object_number = _field_join(fields, "Objektnummer")
    date = _field_join(fields, "Datierung")
    classification = _field_join(fields, "Klassifikation(en)")
    genre = _field_join(fields, "Filmgenre")
    keywords = _field_join(fields, "Schlagwort Film")
    place = _field_join(fields, "Dargestellter Ort")
    country = _field_join(fields, "Produktionsland")
    directors = _field_join(fields, "Regie")
    rights = _field_join(fields, "Rechtsinhaber*in")
    description = _field_join(fields, "Beschreibung", limit=1100)
    subject = "; ".join(
        part
        for part in [
            classification or "Ton/bewegtes Bild - Werk",
            genre,
            keywords,
            place,
            country,
            f"direção: {directors}" if directors else "",
        ]
        if part
    )
    description_parts = [
        description,
        f"objektnummer: {object_number}" if object_number else "",
        f"direção: {directors}" if directors else "",
        f"direitos: {rights}" if rights else "",
        f"catálogo público d:kult: {object_url}",
        (
            "metadado audiovisual público; a página institucional do Filmmuseum Düsseldorf informa que "
            "o acesso ao Filmarchiv é restrito a pesquisa/consulta autorizada e pode envolver taxas. "
            "Não foi detectado player público de vídeo na ficha do objeto."
        ),
    ]
    return {
        "object_id": _object_id_from_url(object_url),
        "object_url": object_url,
        "title": title or _object_id_from_url(object_url),
        "subject": _clean_text(subject, limit=800),
        "description": _clean_text(" | ".join(part for part in description_parts if part), limit=1800),
        "date": date,
        "object_number": object_number,
        "classification": classification,
        "genre": genre,
        "keywords": keywords,
        "place": place,
        "country": country,
    }


def collect_dkult_av_object_links(fetch_html=_fetch_html):
    records = []
    seen = set()
    page_rows = []
    for page in range(1, 60):
        url = DKULT_DUSSELDORF_COLLECTION_PAGE_URL_TEMPLATE.format(page=page)
        html, final_url, status = fetch_html(url, ajax=page > 1)
        page_records = parse_dkult_object_links(html, final_url)
        new_records = []
        for record in page_records:
            if record["object_url"] not in seen:
                seen.add(record["object_url"])
                records.append(record)
                new_records.append(record)
        page_rows.append((final_url, status, len(new_records)))
        if len(records) >= DKULT_DUSSELDORF_EXPECTED_AV_TOTAL or (page > 1 and not new_records):
            break
        time.sleep(0.1)
    return records, page_rows


def collect_filmmuseum_dusseldorf_institutions():
    return [
        {
            "institution": FILMMUSEUM_DUSSELDORF_INSTITUTION_NAME,
            "slug": slugify(FILMMUSEUM_DUSSELDORF_INSTITUTION_NAME),
            "country": FILMMUSEUM_DUSSELDORF_COUNTRY,
            "continent": country_to_continent(FILMMUSEUM_DUSSELDORF_COUNTRY),
            "repository_code": FILMMUSEUM_DUSSELDORF_REPOSITORY_CODE,
            "archive_type": FILMMUSEUM_DUSSELDORF_ARCHIVE_TYPE,
            "filmmuseum_dusseldorf_detail_url": FILMMUSEUM_DUSSELDORF_ARCHIVE_URL,
            "external_url": DKULT_DUSSELDORF_AV_COLLECTION_URL,
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
        "repository_code": FILMMUSEUM_DUSSELDORF_REPOSITORY_CODE,
        "archive_type": FILMMUSEUM_DUSSELDORF_ARCHIVE_TYPE,
        "filmmuseum_dusseldorf_detail_url": FILMMUSEUM_DUSSELDORF_ARCHIVE_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": DKULT_DUSSELDORF_AV_COLLECTION_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": count,
        "embedded_signals": 0,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": DKULT_DUSSELDORF_AV_COLLECTION_URL,
        "platform": FILMMUSEUM_DUSSELDORF_PLATFORM_LABEL,
        "video_link": record.get("object_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_filmmuseum_dusseldorf_dataset(fetch_html=_fetch_html):
    institutions = collect_filmmuseum_dusseldorf_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    try:
        archive_html, archive_url, archive_status = fetch_html(FILMMUSEUM_DUSSELDORF_ARCHIVE_URL)
        has_demo_video = bool(BeautifulSoup(archive_html, "html.parser").find("video"))
        internal_pages.append(
            _internal_page_row(
                institution,
                archive_url,
                "ok",
                archive_status,
                count=1 if has_demo_video else 0,
                warning=(
                    "Página institucional descreve cerca de 20.000 cópias no Filmarchiv, mas informa acesso "
                    "restrito por consulta/pesquisa e taxas; vídeo demonstrativo da página não é tratado como corpus."
                ),
            )
        )
    except Exception as error:
        errors.append(f"página institucional: {error}")
        internal_pages.append(_internal_page_row(institution, FILMMUSEUM_DUSSELDORF_ARCHIVE_URL, "erro", error=str(error)))

    try:
        object_links, page_rows = collect_dkult_av_object_links(fetch_html)
        for page_url, status, count in page_rows:
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "ok",
                    status,
                    count=count,
                    warning="Página de listagem d:kult enumerada por HTML/AJAX público.",
                )
            )
    except Exception as error:
        object_links = []
        errors.append(f"d:kult collection: {error}")
        internal_pages.append(_internal_page_row(institution, DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL, "erro", error=str(error)))

    def fetch_detail(link_record):
        try:
            detail_html, final_url, detail_status = fetch_html(link_record["object_url"])
            return (
                parse_dkult_object_detail(detail_html, final_url, link_record.get("title_hint", "")),
                _internal_page_row(
                    institution,
                    final_url,
                    "ok",
                    detail_status,
                    count=1,
                    warning="Ficha pública de metadado audiovisual no d:kult; mídia aberta não detectada.",
                ),
                "",
            )
        except Exception as error:
            return (
                {
                    "object_id": link_record.get("object_id", ""),
                    "object_url": link_record.get("object_url", ""),
                    "title": link_record.get("title_hint", link_record.get("object_id", "")),
                    "subject": "Ton/bewegtes Bild - Werk",
                    "description": "Objeto audiovisual detectado na listagem d:kult, mas ficha indisponível nesta rodada.",
                    "date": "",
                },
                _internal_page_row(institution, link_record["object_url"], "erro", error=str(error)),
                f"{link_record['object_url']}: {error}",
            )

    detailed_records = []
    with ThreadPoolExecutor(max_workers=DKULT_DUSSELDORF_DETAIL_WORKERS) as executor:
        for record, page_row, error in executor.map(fetch_detail, object_links):
            detailed_records.append(record)
            internal_pages.append(page_row)
            if error:
                errors.append(error)

    rows_video_links = [
        _record_to_video_row(institution, record)
        for record in sorted(detailed_records, key=lambda item: (item.get("date", ""), item.get("title", "")))
    ]
    total_records = len(rows_video_links)
    complete = total_records >= DKULT_DUSSELDORF_MIN_AV_TOTAL
    rows_summary = [
        {
            **_base_row(institution),
            "partner_site": DKULT_DUSSELDORF_AV_COLLECTION_URL,
            "partner_domain": normalize_domain(DKULT_DUSSELDORF_AV_COLLECTION_URL),
            "status": "ok" if total_records else "sem_video_publico",
            "http_code": "200" if total_records else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": DKULT_DUSSELDORF_AV_COLLECTION_OBJECTS_URL,
            "video_links_found_total": total_records,
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": not complete,
            "warning": (
                f"d:kult materializou {total_records} registros públicos da coleção 'Audiovisuelle Dokumente zu Düsseldorf'. "
                "As fichas são metadados audiovisuais públicos; a mídia do Filmarchiv não aparece como streaming aberto "
                "e a página institucional descreve acesso restrito/local mediante consulta autorizada."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, rows_summary, rows_video_links, internal_pages


__all__ = [
    "DKULT_DUSSELDORF_DETAIL_WORKERS",
    "DKULT_DUSSELDORF_EXPECTED_AV_TOTAL",
    "DKULT_DUSSELDORF_MIN_AV_TOTAL",
    "collect_dkult_av_object_links",
    "collect_filmmuseum_dusseldorf_dataset",
    "collect_filmmuseum_dusseldorf_institutions",
    "parse_dkult_object_detail",
    "parse_dkult_object_links",
]
