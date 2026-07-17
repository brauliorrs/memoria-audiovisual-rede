import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CINEMEMOIRE_ARCHIVES_URL,
    CINEMEMOIRE_HOME_URL,
    CINEMEMOIRE_SEARCH_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMEMOIRE_REPOSITORY_CODE = "FR-CINEMEMOIRE"
CINEMEMOIRE_ARCHIVE_TYPE = "Institutional amateur and family film archive"
CINEMEMOIRE_COUNTRY = normalize_country("France")
CINEMEMOIRE_INSTITUTION_NAME = "Cinémémoire"
CINEMEMOIRE_PLATFORM_LABEL = "Cinémémoire"
CINEMEMOIRE_MAX_LIST_PAGES = 4
CINEMEMOIRE_REQUEST_PAUSE = 0.2

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)


def _absolute_url(url):
    return urljoin(CINEMEMOIRE_HOME_URL, str(url or ""))


def collect_cinememoire_institutions():
    return [
        {
            "institution": CINEMEMOIRE_INSTITUTION_NAME,
            "slug": slugify(CINEMEMOIRE_INSTITUTION_NAME),
            "country": CINEMEMOIRE_COUNTRY,
            "continent": country_to_continent(CINEMEMOIRE_COUNTRY),
            "repository_code": CINEMEMOIRE_REPOSITORY_CODE,
            "archive_type": CINEMEMOIRE_ARCHIVE_TYPE,
            "cinememoire_detail_url": CINEMEMOIRE_ARCHIVES_URL,
            "external_url": CINEMEMOIRE_SEARCH_URL,
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
        "repository_code": CINEMEMOIRE_REPOSITORY_CODE,
        "archive_type": CINEMEMOIRE_ARCHIVE_TYPE,
        "cinememoire_detail_url": CINEMEMOIRE_ARCHIVES_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMEMOIRE_SEARCH_URL,
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
        "partner_site": record.get("page_url") or CINEMEMOIRE_SEARCH_URL,
        "platform": CINEMEMOIRE_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def build_cinememoire_list_url(page=1):
    return f"{CINEMEMOIRE_SEARCH_URL}?p={int(page)}"


def parse_cinememoire_list_page(html_text, page_url=CINEMEMOIRE_SEARCH_URL, page_number=1):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for link in soup.find_all("a", href=re.compile(r"^(?:https://cinememoire\.net/)?notice\?num_seq=\d+$")):
        detail_url = _absolute_url(link.get("href"))
        match = re.search(r"num_seq=(\d+)", detail_url)
        if not match:
            continue
        record_id = match.group(1)
        if record_id in seen:
            continue
        seen.add(record_id)
        records.append(
            {
                "record_id": record_id,
                "page_url": detail_url,
                "list_text": _clean_text((link.parent or link).get_text(" ", strip=True), limit=500),
                "page_number": page_number,
                "list_url": page_url,
            }
        )
    return records


def _meta_content(soup, key):
    node = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
    return _clean_text(node.get("content", "")) if node else ""


def _line_values(soup):
    return [_clean_text(line) for line in soup.get_text("\n", strip=True).splitlines() if _clean_text(line)]


def _extract_label(lines, label, stop_labels):
    def normalize_label(value):
        return _clean_text(str(value).rstrip(":").strip())

    normalized_label = normalize_label(label)
    normalized_stop_labels = {normalize_label(value) for value in stop_labels}
    values = []
    collecting = False
    for line in lines:
        normalized_line = normalize_label(line)
        if collecting and normalized_line in normalized_stop_labels:
            break
        if not collecting and normalized_line.startswith(f"{normalized_label} :"):
            value = _clean_text(normalized_line.split(":", 1)[1])
            if value:
                values.append(value)
            collecting = True
            continue
        if collecting:
            values.append(line)
            continue
        if normalized_line == normalized_label:
            collecting = True
    return " | ".join(values)


def _extract_sequence_context(lines):
    for index, line in enumerate(lines):
        if line.startswith("Séquence "):
            return {
                "sequence": line.replace("Séquence ", "", 1).strip(),
                "duration": lines[index + 1] if index + 1 < len(lines) else "",
                "format": lines[index + 2] if index + 2 < len(lines) else "",
                "sound_color": lines[index + 3] if index + 3 < len(lines) else "",
            }
    return {"sequence": "", "duration": "", "format": "", "sound_color": ""}


def parse_cinememoire_notice_page(html_text, page_url=""):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title = _meta_content(soup, "og:title") or _clean_text((soup.find("title") or soup).get_text(" ", strip=True))
    teaser = _meta_content(soup, "og:description") or _meta_content(soup, "twitter:description")
    keywords = _meta_content(soup, "keywords")
    source = soup.find("source", src=True)
    video_link = _absolute_url(source.get("src")) if source else ""
    video_type = source.get("type", "") if source else ""
    poster = ""
    video_tag = soup.find("video")
    if video_tag and video_tag.get("poster"):
        poster = _absolute_url(video_tag.get("poster"))
    poster = poster or _meta_content(soup, "og:image")
    lines = _line_values(soup)
    sequence = _extract_sequence_context(lines)
    stop_labels = {
        "Déposant",
        "Dépôt",
        "Date",
        "Géographie",
        "Genre",
        "Toponymie",
        "Qualite",
        "Qualité",
        "Descripteurs",
        "Professionnel ? Pour plus de fonctionnalités,",
    }
    date = _extract_label(lines, "Date", stop_labels)
    geography = _extract_label(lines, "Géographie", stop_labels)
    genre = _extract_label(lines, "Genre", stop_labels)
    toponymy = _extract_label(lines, "Toponymie", stop_labels)
    descriptors = _extract_label(lines, "Descripteurs", stop_labels)
    subject = "; ".join(value for value in [geography, genre, toponymy, descriptors, keywords] if value)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do catálogo Cinémémoire.",
                f"sequência: {sequence['sequence']}" if sequence["sequence"] else "",
                f"duração: {sequence['duration']}" if sequence["duration"] else "",
                f"formato: {sequence['format']}" if sequence["format"] else "",
                f"som/cor: {sequence['sound_color']}" if sequence["sound_color"] else "",
                f"geografia: {geography}" if geography else "",
                f"gênero: {genre}" if genre else "",
                f"toponímia: {toponymy}" if toponymy else "",
                f"descritores: {descriptors or keywords}" if descriptors or keywords else "",
                f"poster: {poster}" if poster else "",
                f"fonte de vídeo: {video_type}" if video_type else "",
                teaser,
            ]
            if value
        ),
        limit=1400,
    )
    match = re.search(r"num_seq=(\d+)", page_url or "")
    return {
        "record_id": match.group(1) if match else "",
        "source_kind": "cinememoire_notice",
        "video_link": video_link or page_url,
        "page_url": page_url,
        "platform": CINEMEMOIRE_PLATFORM_LABEL,
        "title": title,
        "subject": subject,
        "description": description,
        "date": date,
        "video_title": title,
        "video_subject": subject,
        "video_description": description,
        "video_published_at": date,
        "embedded": bool(video_link),
    }


def collect_cinememoire_dataset():
    institutions = collect_cinememoire_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []

    for url, warning in [
        (CINEMEMOIRE_HOME_URL, "Site institucional Cinémémoire."),
        (CINEMEMOIRE_ARCHIVES_URL, "Página `Archives en lignes`, evidência de filmes em acesso livre."),
        (CINEMEMOIRE_SEARCH_URL, "Busca pública `Archives en ligne`, usada como rota de coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            embedded = len(BeautifulSoup(response.text, "html.parser").find_all(["video", "source", "iframe"]))
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, embedded, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CINEMEMOIRE_MAX_LIST_PAGES + 1):
        list_url = build_cinememoire_list_url(page)
        try:
            response = _fetch(list_url)
            response.raise_for_status()
            listed_records = parse_cinememoire_list_page(response.text, response.url, page)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(listed_records),
                    len(BeautifulSoup(response.text, "html.parser").find_all(["video", "source"])),
                    f"Página {page} da busca pública Cinémémoire.",
                )
            )
        except Exception as error:
            errors.append(f"{list_url}: {error}")
            internal_pages.append(_internal_page_row(institution, list_url, "erro", warning="Falha ao abrir página da busca pública.", error=str(error)))
            continue

        for listed_record in listed_records:
            record_id = listed_record["record_id"]
            if record_id in records_by_id:
                continue
            try:
                detail_response = _fetch(listed_record["page_url"])
                detail_response.raise_for_status()
                parsed = parse_cinememoire_notice_page(detail_response.text, detail_response.url)
                records_by_id[record_id] = {**listed_record, **parsed}
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        detail_response.url,
                        "ok",
                        detail_response.status_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública Cinémémoire verificada, com vídeo HTML5 registrado sem baixar mídia.",
                    )
                )
            except Exception as error:
                errors.append(f"{listed_record['page_url']}: {error}")
                internal_pages.append(_internal_page_row(institution, listed_record["page_url"], "erro", warning="Falha ao abrir ficha pública Cinémémoire.", error=str(error)))
            time.sleep(CINEMEMOIRE_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("video_link")]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEMEMOIRE_SEARCH_URL,
            "partner_domain": normalize_domain(CINEMEMOIRE_SEARCH_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": CINEMEMOIRE_SEARCH_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                f"Janela técnica MVP: primeiras {CINEMEMOIRE_MAX_LIST_PAGES} páginas da busca pública, "
                "com fichas `notice` e vídeos HTML5/MP4 expostos. Não é o catálogo integral do Cinémémoire."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMEMOIRE_ARCHIVE_TYPE",
    "CINEMEMOIRE_COUNTRY",
    "CINEMEMOIRE_INSTITUTION_NAME",
    "CINEMEMOIRE_PLATFORM_LABEL",
    "CINEMEMOIRE_REPOSITORY_CODE",
    "build_cinememoire_list_url",
    "collect_cinememoire_dataset",
    "collect_cinememoire_institutions",
    "parse_cinememoire_list_page",
    "parse_cinememoire_notice_page",
]
