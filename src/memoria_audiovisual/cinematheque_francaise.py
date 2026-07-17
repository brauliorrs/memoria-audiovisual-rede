import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL, CINEMATHEQUE_FRANCAISE_HENRI_URL, HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMATHEQUE_FRANCAISE_REPOSITORY_CODE = "FR-CINEMATHEQUE-FRANCAISE"
CINEMATHEQUE_FRANCAISE_ARCHIVE_TYPE = "National cinematheque and online film streaming platform"
CINEMATHEQUE_FRANCAISE_COUNTRY = normalize_country("France")
CINEMATHEQUE_FRANCAISE_INSTITUTION_NAME = "Cinémathèque française / Musée du cinéma"
CINEMATHEQUE_FRANCAISE_PLATFORM_LABEL = "HENRI"
CINEMATHEQUE_FRANCAISE_MAX_DETAIL_PAGES = 24
CINEMATHEQUE_FRANCAISE_DETAIL_WORKERS = 4

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    raw = str(value or "")
    if "<" in raw and ">" in raw:
        raw = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)
    text = re.sub(r"\s+", " ", raw).strip()
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


def _decode_response(response):
    return response.content.decode("utf-8", errors="replace")


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def collect_cinematheque_francaise_institutions():
    return [
        {
            "institution": CINEMATHEQUE_FRANCAISE_INSTITUTION_NAME,
            "slug": slugify(CINEMATHEQUE_FRANCAISE_INSTITUTION_NAME),
            "country": CINEMATHEQUE_FRANCAISE_COUNTRY,
            "continent": country_to_continent(CINEMATHEQUE_FRANCAISE_COUNTRY),
            "repository_code": CINEMATHEQUE_FRANCAISE_REPOSITORY_CODE,
            "archive_type": CINEMATHEQUE_FRANCAISE_ARCHIVE_TYPE,
            "cinematheque_francaise_detail_url": CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL,
            "external_url": CINEMATHEQUE_FRANCAISE_HENRI_URL,
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
        "repository_code": CINEMATHEQUE_FRANCAISE_REPOSITORY_CODE,
        "archive_type": CINEMATHEQUE_FRANCAISE_ARCHIVE_TYPE,
        "cinematheque_francaise_detail_url": CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMATHEQUE_FRANCAISE_HENRI_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cinematheque_francaise_henri_list(html_text, page_url=CINEMATHEQUE_FRANCAISE_HENRI_URL):
    records = []
    seen = set()
    pattern = re.compile(
        r"<li class=\"?film(?:\s+archived)?\"?>\s*<a href=(film/[^>\s]+)[^>]*>(.*?)(?=<li class=\"?film|</main>|</body>|$)",
        re.S,
    )
    for href, segment in pattern.findall(html_text or ""):
        record_id_match = re.search(r"film/(\d+)-", href)
        if not record_id_match:
            continue
        record_id = record_id_match.group(1)
        if record_id in seen:
            continue
        seen.add(record_id)
        is_archived = "Film indisponible" in segment or "film archived" in segment
        title_match = re.search(r"<div class=titre>(.*?)</div>", segment, re.S)
        duration_match = re.search(r"<div class=duree>(.*?)</div>", segment, re.S)
        meta_candidates = re.findall(r"<div>([^<>]*,\s*(?:18|19|20)\d{2}[^<>]*)</div>", segment)
        meta = _clean_text(meta_candidates[0] if meta_candidates else "")
        title = _clean_text(title_match.group(1) if title_match else "")
        duration = _clean_text(duration_match.group(1) if duration_match else "")
        creator = _clean_text(re.sub(r",\s*(?:18|19|20)\d{2}.*$", "", meta))
        year = _extract_year(meta)
        if is_archived:
            continue
        records.append(
            {
                "record_id": record_id,
                "source_kind": "cinematheque_francaise_henri_listing_record",
                "page_url": urljoin(page_url, href),
                "video_link": urljoin(page_url, href),
                "platform": CINEMATHEQUE_FRANCAISE_PLATFORM_LABEL,
                "title": title,
                "subject": creator,
                "description": _clean_text(
                    "Ficha pública HENRI da Cinémathèque française."
                    + (f" duração: {duration}." if duration else ""),
                    limit=1000,
                ),
                "date": year,
                "embedded": False,
            }
        )
    return records


def parse_cinematheque_francaise_henri_detail(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    iframe = soup.find("iframe", src=re.compile(r"player\.vimeo\.com/video/", re.I))
    embed_url = iframe.get("src", "") if iframe else ""
    title = _clean_text((soup.find("h1") or soup.find("title") or "").get_text(" ", strip=True), limit=250)
    text_lines = [_clean_text(line) for line in soup.get_text("\n", strip=True).splitlines() if _clean_text(line)]
    title_index = text_lines.index(title) if title in text_lines else -1
    creator = text_lines[title_index + 1] if title_index >= 0 and title_index + 1 < len(text_lines) else ""
    metadata = text_lines[title_index + 2] if title_index >= 0 and title_index + 2 < len(text_lines) else ""
    description = " ".join(text_lines[title_index + 3 : title_index + 7]) if title_index >= 0 else ""
    unavailable = "Ce film n'est plus visible sur HENRI" in (html_text or "")
    return {
        "record_id": re.search(r"/film/(\d+)-", page_url).group(1) if re.search(r"/film/(\d+)-", page_url) else "",
        "source_kind": "cinematheque_francaise_henri_detail_record",
        "page_url": page_url,
        "video_link": embed_url or page_url,
        "platform": CINEMATHEQUE_FRANCAISE_PLATFORM_LABEL,
        "title": title,
        "subject": _clean_text("; ".join(value for value in [creator, metadata] if value), limit=700),
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    "Film publicado em HENRI, plataforma de streaming gratuito da Cinémathèque française.",
                    f"embed: {embed_url}" if embed_url else "",
                    "film indisponível no momento da coleta" if unavailable else "",
                    description,
                ]
                if value
            ),
            limit=1800,
        ),
        "date": _extract_year(metadata),
        "embedded": bool(embed_url),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CINEMATHEQUE_FRANCAISE_HENRI_URL,
        "platform": CINEMATHEQUE_FRANCAISE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_detail(record):
    response = _fetch(record["page_url"])
    response.raise_for_status()
    return parse_cinematheque_francaise_henri_detail(_decode_response(response), response.url), response.url, response.status_code


def collect_cinematheque_francaise_dataset():
    institutions = collect_cinematheque_francaise_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []

    try:
        response = _fetch(CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL)
        response.raise_for_status()
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                warning="Página institucional de coleções; declara mais de 40.000 filmes e delimita HENRI como streaming gratuito.",
            )
        )
    except Exception as error:
        errors.append(f"{CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL}: {error}")
        internal_pages.append(_internal_page_row(institution, CINEMATHEQUE_FRANCAISE_COLLECTIONS_URL, "erro", error=str(error)))

    try:
        response = _fetch(CINEMATHEQUE_FRANCAISE_HENRI_URL)
        response.raise_for_status()
        html_text = _decode_response(response)
        records = parse_cinematheque_francaise_henri_list(html_text, response.url)
        for record in records:
            records_by_id[record["record_id"]] = record
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(records),
                0,
                "Listagem pública HENRI; filmes indisponíveis são excluídos do corpus ativo.",
            )
        )
    except Exception as error:
        errors.append(f"{CINEMATHEQUE_FRANCAISE_HENRI_URL}: {error}")
        internal_pages.append(_internal_page_row(institution, CINEMATHEQUE_FRANCAISE_HENRI_URL, "erro", error=str(error)))

    with ThreadPoolExecutor(max_workers=CINEMATHEQUE_FRANCAISE_DETAIL_WORKERS) as executor:
        futures = [
            executor.submit(_fetch_detail, record)
            for record in list(records_by_id.values())[:CINEMATHEQUE_FRANCAISE_MAX_DETAIL_PAGES]
        ]
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
                        "Ficha pública HENRI aberta para metadados e player Vimeo.",
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
            "partner_site": CINEMATHEQUE_FRANCAISE_HENRI_URL,
            "partner_domain": normalize_domain(CINEMATHEQUE_FRANCAISE_HENRI_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CINEMATHEQUE_FRANCAISE_HENRI_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte público HENRI da Cinémathèque française. "
                "A instituição declara mais de 40.000 filmes em seu acervo físico, mas o organismo materializa "
                f"{len(records)} registros disponíveis na superfície pública HENRI e enriquece até "
                f"{CINEMATHEQUE_FRANCAISE_MAX_DETAIL_PAGES} fichas, sem baixar mídia e sem afirmar cobertura total."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMATHEQUE_FRANCAISE_ARCHIVE_TYPE",
    "CINEMATHEQUE_FRANCAISE_COUNTRY",
    "CINEMATHEQUE_FRANCAISE_INSTITUTION_NAME",
    "CINEMATHEQUE_FRANCAISE_MAX_DETAIL_PAGES",
    "CINEMATHEQUE_FRANCAISE_PLATFORM_LABEL",
    "CINEMATHEQUE_FRANCAISE_REPOSITORY_CODE",
    "collect_cinematheque_francaise_dataset",
    "collect_cinematheque_francaise_institutions",
    "parse_cinematheque_francaise_henri_detail",
    "parse_cinematheque_francaise_henri_list",
]
