from __future__ import annotations

import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CNA_ACCESS_FORM_URL,
    CNA_ACCESS_URL,
    CNA_COLLECTIONS_URL,
    CNA_HOME_URL,
    CNA_RESULTS_NAV_URL_TEMPLATE,
    CNA_SEARCH_PROFILE_URL,
    CNA_SEARCH_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain
from .geography import country_to_continent, normalize_country


CNA_REPOSITORY_CODE = "LU-CNA"
CNA_ARCHIVE_TYPE = "National audiovisual archive"
CNA_COUNTRY = normalize_country("Luxembourg")
CNA_INSTITUTION_NAME = "Centre national de l'audiovisuel (CNA)"
CNA_PLATFORM_LABEL = "CNAsearch"
CNA_PROFILE_LABEL = "Philippe Schneider, réalisateur"
CNA_MAX_RESULT_PAGES = 6
CNA_REQUEST_PAUSE = 0.12

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})

CNA_DETAIL_LABELS = [
    "Média",
    "Numéro d’objet",
    "Titre",
    "Genre",
    "Description détaillée",
    "Synopsis (résumé)",
    "Découpage technique",
    "Date",
    "Pays",
    "Crédits",
    "Sujet",
    "Mot-clé géographique",
    "Forme",
    "Langue du contenu",
    "Nature du document",
    "Navigateur hiérarchique",
]


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).replace("\u200e", "").strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)


def collect_cna_institutions():
    return [
        {
            "institution": CNA_INSTITUTION_NAME,
            "slug": "cna-luxembourg",
            "country": CNA_COUNTRY,
            "continent": country_to_continent(CNA_COUNTRY),
            "repository_code": CNA_REPOSITORY_CODE,
            "archive_type": CNA_ARCHIVE_TYPE,
            "cna_detail_url": CNA_HOME_URL,
            "external_url": CNA_SEARCH_PROFILE_URL,
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
        "repository_code": CNA_REPOSITORY_CODE,
        "archive_type": CNA_ARCHIVE_TYPE,
        "cna_detail_url": CNA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CNA_SEARCH_PROFILE_URL,
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
        "partner_site": CNA_SEARCH_PROFILE_URL,
        "platform": CNA_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def parse_cna_result_page(html_text, page_url=""):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for anchor in soup.select('a[href*="/Details/film/"]'):
        href = urljoin(page_url or CNA_SEARCH_PROFILE_URL, anchor.get("href", ""))
        record_id = href.rstrip("/").rsplit("/", 1)[-1]
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        records.append(
            {
                "record_id": record_id,
                "page_url": href,
                "list_text": _clean_text(anchor.get_text(" ", strip=True), limit=700),
            }
        )
    return records


def extract_cna_result_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"Images animées et enregistrements audio\s+([\d\s.,]+)\s+Résultats", text)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def extract_cna_declared_pages(html_text):
    pages = [int(match) for match in re.findall(r"/resultsnavigate/(\d+)", html_text or "")]
    return max(pages) if pages else 1


def _detail_lines(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text("\n", strip=True)
    for label in sorted(CNA_DETAIL_LABELS, key=len, reverse=True):
        text = re.sub(rf"(?<![\n(])\b{re.escape(label)}\b", f"\n{label}\n", text)
    lines = [_clean_text(line) for line in text.split("\n")]
    return [line for line in lines if line and line not in {"Retirer de la sélection", "Ajouter à la sélection"}]


def _extract_metadata(lines):
    metadata = {}
    labels = set(CNA_DETAIL_LABELS)
    for index, line in enumerate(lines):
        if line not in labels:
            continue
        values = []
        next_index = index + 1
        while next_index < len(lines):
            next_line = lines[next_index]
            if next_line in labels or next_line in {"Contact", "Plan du site", "Accessibilité", "Aspects Légaux"}:
                break
            values.append(next_line)
            next_index += 1
        metadata[line] = _clean_text(" ".join(values), limit=1200)
    return metadata


def _extract_title(metadata, soup):
    title = metadata.get("Titre", "")
    title = re.split(r"\s+\(Titre (?:privilégié|propre|alternatif)\)", title)[0]
    if title:
        return _clean_text(title)
    h1 = soup.find("h1")
    return _clean_text(h1.get_text(" ", strip=True)) if h1 else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def parse_cna_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    lines = _detail_lines(html_text)
    metadata = _extract_metadata(lines)
    source = soup.find("source", src=True)
    media_source = _clean_text(source.get("src", "")) if source else ""
    media_type = _clean_text(source.get("type", "")) if source else ""
    nature = metadata.get("Nature du document", "")
    description_detail = metadata.get("Description détaillée", "")
    synopsis = metadata.get("Synopsis (résumé)", "")
    technical = metadata.get("Découpage technique", "")
    genre = metadata.get("Genre", "")
    form = metadata.get("Forme", "")
    credits = metadata.get("Crédits", "")
    subject = "; ".join(value for value in [metadata.get("Sujet", ""), metadata.get("Mot-clé géographique", ""), genre, form] if value)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                f"Ficha pública CNAsearch no perfil `{CNA_PROFILE_LABEL}`.",
                f"número de objeto: {metadata.get('Numéro d’objet', '')}" if metadata.get("Numéro d’objet") else "",
                f"natureza: {nature}" if nature else "",
                f"gênero: {genre}" if genre else "",
                f"forma: {form}" if form else "",
                f"país: {metadata.get('Pays', '')}" if metadata.get("Pays") else "",
                f"créditos: {credits}" if credits else "",
                f"fonte de mídia: {media_type}" if media_type else "",
                description_detail,
                synopsis,
                technical,
            ]
            if value
        ),
        limit=1600,
    )
    record_id = page_url.rstrip("/").rsplit("/", 1)[-1]
    return {
        "record_id": record_id,
        "source_kind": "cna_search_profile_record",
        "video_link": media_source or page_url,
        "page_url": page_url,
        "platform": CNA_PLATFORM_LABEL,
        "title": _extract_title(metadata, soup),
        "subject": _clean_text(subject, limit=700),
        "description": description,
        "date": _extract_year(metadata.get("Date", "")),
        "embedded": bool(media_source),
        "is_moving_image": "image animée" in nature.lower() or bool(media_source),
    }


def _collect_result_pages(institution, internal_pages, errors):
    records_by_id = {}
    declared_total = 0
    declared_pages = 1
    try:
        response = _fetch(CNA_SEARCH_PROFILE_URL)
        response.raise_for_status()
        declared_total = extract_cna_result_total(response.text)
        declared_pages = extract_cna_declared_pages(response.text)
        first_records = parse_cna_result_page(response.text, response.url)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(first_records),
                0,
                f"Perfil público CNAsearch `{CNA_PROFILE_LABEL}` iniciado por rota estável.",
            )
        )
    except Exception as error:
        errors.append(f"{CNA_SEARCH_PROFILE_URL}: {error}")
        internal_pages.append(_internal_page_row(institution, CNA_SEARCH_PROFILE_URL, "erro", warning="Falha ao abrir perfil público CNAsearch.", error=str(error)))
        return records_by_id, declared_total, declared_pages

    for record in first_records:
        records_by_id[record["record_id"]] = record

    max_pages = min(max(declared_pages, 1), CNA_MAX_RESULT_PAGES)
    for page in range(2, max_pages + 1):
        page_url = CNA_RESULTS_NAV_URL_TEMPLATE.format(page=page)
        try:
            response = _fetch(page_url)
            response.raise_for_status()
            page_records = parse_cna_result_page(response.text, response.url)
            for record in page_records:
                records_by_id.setdefault(record["record_id"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    0,
                    f"Página {page} do perfil público CNAsearch `{CNA_PROFILE_LABEL}`.",
                )
            )
        except Exception as error:
            errors.append(f"{page_url}: {error}")
            internal_pages.append(_internal_page_row(institution, page_url, "erro", warning="Falha ao navegar página de resultados CNAsearch.", error=str(error)))
        time.sleep(CNA_REQUEST_PAUSE)

    return records_by_id, declared_total, declared_pages


def collect_cna_dataset():
    institutions = collect_cna_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    for url, warning in [
        (CNA_HOME_URL, "Site institucional do Centre national de l'audiovisuel."),
        (CNA_COLLECTIONS_URL, "Página oficial sobre coleções, incluindo imagens animadas."),
        (CNA_ACCESS_URL, "Página oficial de acesso; aponta CNAsearch e descreve consulta/reuso."),
        (CNA_ACCESS_FORM_URL, "Formulário oficial de consulta para materiais de acervo."),
        (CNA_SEARCH_URL, "Busca simples do CNAsearch; sondada como contexto, sem POST por instabilidade WAF."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    listed_records, declared_total, declared_pages = _collect_result_pages(institution, internal_pages, errors)
    records = []
    for listed_record in listed_records.values():
        try:
            response = _fetch(listed_record["page_url"])
            response.raise_for_status()
            parsed = parse_cna_detail_page(response.text, response.url)
            if not parsed.get("is_moving_image"):
                continue
            record = {**listed_record, **parsed}
            records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    1 if parsed.get("embedded") else 0,
                    "Ficha pública CNAsearch verificada, com fonte MP4 registrada quando exposta.",
                )
            )
        except Exception as error:
            errors.append(f"{listed_record['page_url']}: {error}")
            internal_pages.append(_internal_page_row(institution, listed_record["page_url"], "erro", warning="Falha ao abrir ficha pública CNAsearch.", error=str(error)))
        time.sleep(CNA_REQUEST_PAUSE)

    video_links = [_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CNA_SEARCH_PROFILE_URL,
            "partner_domain": normalize_domain(CNA_SEARCH_PROFILE_URL),
            "status": "ok" if records else "erro",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "instavel",
            "final_url": CNA_SEARCH_PROFILE_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo perfil público CNAsearch "
                f"`{CNA_PROFILE_LABEL}`. O perfil declarou {declared_total or 'múltiplos'} resultados "
                f"em até {declared_pages or 'múltiplas'} páginas; o MVP materializa {len(records)} "
                "registros de imagem em movimento desse perfil, sem baixar mídia e sem afirmar catálogo total do CNA."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CNA_ARCHIVE_TYPE",
    "CNA_COUNTRY",
    "CNA_INSTITUTION_NAME",
    "CNA_MAX_RESULT_PAGES",
    "CNA_PLATFORM_LABEL",
    "CNA_PROFILE_LABEL",
    "CNA_REPOSITORY_CODE",
    "collect_cna_dataset",
    "collect_cna_institutions",
    "extract_cna_declared_pages",
    "extract_cna_result_total",
    "parse_cna_detail_page",
    "parse_cna_result_page",
]
