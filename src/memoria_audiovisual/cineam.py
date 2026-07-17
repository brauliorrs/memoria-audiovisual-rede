import html
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CINEAM_ABOUT_URL,
    CINEAM_DEPOSIT_URL,
    CINEAM_FILMS_URL,
    CINEAM_HOME_URL,
    CINEAM_REALISATIONS_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain
from .geography import country_to_continent, normalize_country


CINEAM_REPOSITORY_CODE = "FR-CINEAM"
CINEAM_ARCHIVE_TYPE = "Institutional amateur film and audiovisual archive"
CINEAM_COUNTRY = normalize_country("France")
CINEAM_INSTITUTION_NAME = "CINÉAM"
CINEAM_PLATFORM_LABEL = "CINÉAM"
CINEAM_MAX_LIST_PAGES = 2
CINEAM_REQUEST_PAUSE = 0.8

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url, **kwargs):
    response = None
    for attempt in range(4):
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)
        if response.status_code not in {429, 503}:
            return response
        time.sleep(1.5 * (attempt + 1))
    return response


def _absolute_url(url):
    return urljoin(CINEAM_HOME_URL, str(url or ""))


def collect_cineam_institutions():
    return [
        {
            "institution": CINEAM_INSTITUTION_NAME,
            "slug": "cineam",
            "country": CINEAM_COUNTRY,
            "continent": country_to_continent(CINEAM_COUNTRY),
            "repository_code": CINEAM_REPOSITORY_CODE,
            "archive_type": CINEAM_ARCHIVE_TYPE,
            "cineam_detail_url": CINEAM_HOME_URL,
            "external_url": CINEAM_FILMS_URL,
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
        "repository_code": CINEAM_REPOSITORY_CODE,
        "archive_type": CINEAM_ARCHIVE_TYPE,
        "cineam_detail_url": CINEAM_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEAM_FILMS_URL,
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
        "partner_site": CINEAM_FILMS_URL,
        "platform": CINEAM_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _extract_onclick_url(item, base_url):
    match = re.search(r"document\.location\.href='([^']+)'", item.get("onclick", ""))
    return urljoin(base_url, html.unescape(match.group(1))) if match else ""


def _parse_list_text(text):
    match = re.match(r"(.+?)\s+((?:19|20)\d{2})\s+\|\s+(.+)$", text)
    if not match:
        return "", "", ""
    return tuple(_clean_text(part) for part in match.groups())


def parse_cineam_list_page(html_text, page_url=CINEAM_FILMS_URL, page_number=1):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for item in soup.select("article.diaListItem"):
        detail_url = _extract_onclick_url(item, page_url)
        record_id = item.get("data-diaref", "").strip().lstrip("-")
        if not detail_url or not record_id or record_id in seen:
            continue
        seen.add(record_id)
        list_text = _clean_text(item.get_text(" ", strip=True), limit=500)
        title, year, director = _parse_list_text(list_text)
        thumb = item.find("img")
        records.append(
            {
                "record_id": record_id,
                "page_url": detail_url,
                "list_text": list_text,
                "title": title,
                "date": year,
                "director": director,
                "thumbnail": thumb.get("src", "") if thumb else "",
                "page_number": page_number,
            }
        )
    return records


def _parse_declared_pages(html_text):
    pages = [int(match) for match in re.findall(r"[?&]page=(\d+)", html_text or "")]
    return max(pages) if pages else 0


def _extract_embed_url(soup):
    for iframe in soup.find_all("iframe", src=True):
        src = iframe.get("src", "")
        if "diazcineam.oembed.diazinteregio.org/embed/" in src:
            return src
    return ""


def _extract_video_source(embed_html, embed_url=""):
    soup = BeautifulSoup(embed_html or "", "html.parser")
    for source in soup.find_all("source", src=True):
        src = source.get("src", "")
        if src:
            return urljoin(embed_url, src), source.get("type", "")
    return "", ""


def _extract_label(text, label, stop_labels):
    stop = "|".join(re.escape(stop_label) for stop_label in stop_labels)
    match = re.search(rf"{re.escape(label)}\s+(.*?)(?=\s+(?:{stop})\s+|$)", text)
    return _clean_text(match.group(1)) if match else ""


def _split_duration_and_keywords(value):
    text = _clean_text(value)
    match = re.match(r"(\d{1,2}:\d{2}(?::\d{2})?)(.*)", text)
    if not match:
        return text, ""
    duration = match.group(1)
    keywords = match.group(2)
    for marker in ["Ajouter à mes sélections", "Envoyer un commentaire"]:
        keywords = keywords.replace(marker, "")
    return duration, _clean_text(keywords, limit=400)


def _trim_interface_tail(value):
    text = str(value or "")
    for marker in [
        "Suggestions Ici les suggestions",
        "Sauvegarder ma recherche",
        "Nom de votre recherche sauvegardée",
        "Votre recherche sauvegardée",
        "Choix de la sélection",
        "Envoyer un commentaire",
        "Recherche avancée",
        "S'identifier",
        "Inscrivez-vous à la newsletter",
    ]:
        text = text.split(marker, 1)[0]
    return _clean_text(text, limit=900)


def parse_cineam_film_page(html_text, page_url="", embed_html=""):
    soup = BeautifulSoup(html_text or "", "html.parser")
    h1_values = [_clean_text(h1.get_text(" ", strip=True)) for h1 in soup.find_all("h1")]
    title = h1_values[1] if len(h1_values) > 1 else (h1_values[0] if h1_values else "")
    text = _clean_text(soup.get_text(" ", strip=True))
    labels = ["Réalisation", "Année", "Format", "Son", "Coloration", "Durée", "Résumé", "Suggestions"]
    director = _extract_label(text, "Réalisation", labels[1:])
    year = _extract_label(text, "Année", labels[2:])
    film_format = _extract_label(text, "Format", labels[3:])
    sound = _extract_label(text, "Son", labels[4:])
    color = _extract_label(text, "Coloration", labels[5:])
    duration, keywords = _split_duration_and_keywords(_extract_label(text, "Durée", labels[6:]))
    summary = _trim_interface_tail(_extract_label(text, "Résumé", labels[7:]))
    embed_url = _extract_embed_url(soup)
    video_source, video_type = _extract_video_source(embed_html, embed_url)
    record_match = re.search(r"_doc=(?:9%3A4%3A|9:4:)(\d+)", page_url)
    record_id = record_match.group(1) if record_match else ""
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do catálogo CINÉAM / DiazInteregio.",
                f"realização: {director}" if director else "",
                f"formato: {film_format}" if film_format else "",
                f"som: {sound}" if sound else "",
                f"coloração: {color}" if color else "",
                f"duração: {duration}" if duration else "",
                f"descritores: {keywords}" if keywords else "",
                f"embed: {embed_url}" if embed_url else "",
                f"fonte de vídeo: {video_type}" if video_type else "",
                summary,
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": record_id,
        "source_kind": "cineam_film",
        "video_link": video_source or embed_url or page_url,
        "page_url": page_url,
        "platform": CINEAM_PLATFORM_LABEL,
        "title": title,
        "subject": "; ".join(value for value in [director, keywords] if value),
        "description": description,
        "date": year,
        "embedded": bool(video_source or embed_url),
    }


def collect_cineam_dataset():
    institutions = collect_cineam_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []
    declared_pages = 0

    for url, warning in [
        (CINEAM_HOME_URL, "Site institucional CINÉAM."),
        (CINEAM_ABOUT_URL, "Página sobre missão, descrição dos filmes e uso da base Diaz."),
        (CINEAM_DEPOSIT_URL, "Página sobre depósito, salvaguarda e preservação de filmes."),
        (CINEAM_FILMS_URL, "Listagem pública `Films / Exploration`, usada como rota de coleta."),
        (CINEAM_REALISATIONS_URL, "Página de realizações e ações audiovisuais; contexto, não rota principal da coleta."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    for page in range(1, CINEAM_MAX_LIST_PAGES + 1):
        list_url = CINEAM_FILMS_URL if page == 1 else f"{CINEAM_FILMS_URL}?page={page}"
        try:
            response = _fetch(list_url)
            response.raise_for_status()
            if page == 1:
                declared_pages = _parse_declared_pages(response.text)
            listed_records = parse_cineam_list_page(response.text, response.url, page)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(listed_records),
                    0,
                    f"Página {page} da listagem pública `Films / Exploration` do CINÉAM.",
                )
            )
        except Exception as error:
            errors.append(f"{list_url}: {error}")
            internal_pages.append(_internal_page_row(institution, list_url, "erro", warning="Falha ao abrir listagem pública CINÉAM.", error=str(error)))
            continue

        for listed_record in listed_records:
            record_id = listed_record["record_id"]
            if record_id in records_by_id:
                continue
            try:
                detail_response = _fetch(listed_record["page_url"])
                detail_response.raise_for_status()
                detail_soup = BeautifulSoup(detail_response.text, "html.parser")
                embed_url = _extract_embed_url(detail_soup)
                embed_html = ""
                if embed_url:
                    try:
                        embed_response = _fetch(embed_url)
                        embed_response.raise_for_status()
                        embed_html = embed_response.text
                    except Exception as error:
                        errors.append(f"{embed_url}: {error}")
                parsed = parse_cineam_film_page(detail_response.text, detail_response.url, embed_html)
                parsed["title"] = parsed.get("title") or listed_record.get("title", "")
                parsed["date"] = parsed.get("date") or listed_record.get("date", "")
                parsed["subject"] = parsed.get("subject") or listed_record.get("director", "")
                records_by_id[record_id] = {**listed_record, **parsed}
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        detail_response.url,
                        "ok",
                        detail_response.status_code,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública CINÉAM verificada, com embed Diaz registrado sem baixar mídia.",
                    )
                )
            except Exception as error:
                errors.append(f"{listed_record['page_url']}: {error}")
                internal_pages.append(_internal_page_row(institution, listed_record["page_url"], "erro", warning="Falha ao abrir ficha pública CINÉAM.", error=str(error)))
            time.sleep(CINEAM_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEAM_FILMS_URL,
            "partner_domain": normalize_domain(CINEAM_FILMS_URL),
            "status": "ok" if records else "erro",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "instavel",
            "final_url": CINEAM_FILMS_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado por listagem pública `Films / Exploration`. "
                f"A paginação pública indicou até {declared_pages or 'múltiplas'} páginas; o MVP materializa "
                f"{len(records)} registros nas primeiras {CINEAM_MAX_LIST_PAGES} páginas, sem baixar mídia "
                "e sem afirmar catálogo total."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEAM_ARCHIVE_TYPE",
    "CINEAM_COUNTRY",
    "CINEAM_INSTITUTION_NAME",
    "CINEAM_MAX_LIST_PAGES",
    "CINEAM_PLATFORM_LABEL",
    "CINEAM_REPOSITORY_CODE",
    "collect_cineam_dataset",
    "collect_cineam_institutions",
    "parse_cineam_film_page",
    "parse_cineam_list_page",
]
