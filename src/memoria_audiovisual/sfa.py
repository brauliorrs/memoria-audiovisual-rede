import re
from collections import deque
from urllib.parse import parse_qs, urlparse

import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

from .config import (
    HEADERS,
    REQUEST_TIMEOUT,
    SFA_ENGLISH_URL,
    SFA_HOME_URL,
    SFA_VAC_FUND_URL,
    SFA_VAC_HOME_URL,
    SFA_VAC_RECORD_URL_TEMPLATE,
    SFA_VAC_SEARCH_URL,
)
from .crawler import slugify
from .geography import country_to_continent, normalize_country


SFA_REPOSITORY_CODE = "SI-AS-1086"
SFA_ARCHIVE_TYPE = "Institutional film archive"
SFA_COUNTRY = normalize_country("Slovenia")
SFA_INSTITUTION_NAME = "Arhiv Republike Slovenije - Slovenski filmski arhiv"
SFA_PLATFORM_LABEL = "VAC"
SFA_FUND_RECORD_ID = "25366"
SFA_SEED_RECORD_IDS = ["388739", "389406"]
SFA_MAX_SAMPLE_RECORDS = 8

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "sl-SI,sl;q=0.9,en;q=0.8,pt-BR;q=0.7"})
urllib3.disable_warnings(InsecureRequestWarning)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _vac_get(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, verify=False)


def _get_record_id(url):
    parsed = urlparse(url)
    return (parse_qs(parsed.query).get("id") or [""])[0]


def collect_sfa_institutions():
    return [
        {
            "institution": SFA_INSTITUTION_NAME,
            "slug": slugify(SFA_INSTITUTION_NAME),
            "country": SFA_COUNTRY,
            "continent": country_to_continent(SFA_COUNTRY),
            "repository_code": SFA_REPOSITORY_CODE,
            "archive_type": SFA_ARCHIVE_TYPE,
            "sfa_detail_url": SFA_HOME_URL,
            "external_url": SFA_VAC_FUND_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _label_values_from_vac_detail(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    values = {}
    for row in soup.select("div.row"):
        labels = [_clean_text(label.get_text(" ", strip=True)) for label in row.select("label.form-control-label")]
        labels = [label for label in labels if label]
        if len(labels) < 2 or not labels[0].endswith(":"):
            continue
        key = labels[0].rstrip(":")
        value = labels[1]
        if key in values and value:
            values[key] = f"{values[key]}; {value}"
        elif value:
            values[key] = value
    return values


def _tree_neighbors_from_vac_detail(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    neighbors = []
    for div_id in ("archivePlanTreePrevData", "archivePlanTreeNextData"):
        for node in soup.select(f"#{div_id} ul[data-id][data-title]"):
            title = _clean_text(node.get("data-title"))
            if title.startswith("SI AS 1086/"):
                neighbors.append(node.get("data-id"))
    return [record_id for record_id in neighbors if record_id]


def _subject_from_metadata(metadata):
    parts = []
    for key in ("Zvrst filma", "Podzvrst filma", "Vrsta filma glede na dolžino"):
        if metadata.get(key):
            parts.append(metadata[key])
    return " | ".join(dict.fromkeys(parts))


def _description_from_metadata(metadata):
    parts = [
        "Ficha pública de metadados filmográficos no VAČ, sem player detectado na ficha.",
        f"conteúdo: {metadata.get('Vsebina PE', '')}" if metadata.get("Vsebina PE") else "",
        f"responsáveis: {metadata.get('Odgovorna oseba za nastanek PE', '')}"
        if metadata.get("Odgovorna oseba za nastanek PE")
        else "",
        f"quantidade: {metadata.get('Količina PE', '')}" if metadata.get("Količina PE") else "",
        f"suporte: {metadata.get('Zvrsti arhivskega gradiva', '')}"
        if metadata.get("Zvrsti arhivskega gradiva")
        else "",
        f"nível: {metadata.get('Nivo popisa', '')}" if metadata.get("Nivo popisa") else "",
    ]
    return _clean_text(" | ".join(part for part in parts if part), limit=900)


def parse_sfa_vac_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    metadata = _label_values_from_vac_detail(html_text)
    heading = _clean_text((soup.find("h3") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    title = metadata.get("Naslov PE") or re.sub(r"^SI AS 1086/\d+\s+", "", heading)
    record_id = _get_record_id(page_url)
    return {
        "record_id": record_id,
        "source_kind": "vac_film_record",
        "video_link": page_url,
        "platform": SFA_PLATFORM_LABEL,
        "title": title,
        "subject": _subject_from_metadata(metadata),
        "description": _description_from_metadata(metadata),
        "date": metadata.get("Čas nastanka PE", ""),
        "embedded": False,
        "signature": metadata.get("Signatura PE", ""),
        "neighbors": _tree_neighbors_from_vac_detail(html_text),
    }


def parse_sfa_vac_fund_page(html_text, page_url=SFA_VAC_FUND_URL):
    metadata = _label_values_from_vac_detail(html_text)
    return {
        "record_id": _get_record_id(page_url) or SFA_FUND_RECORD_ID,
        "signature": metadata.get("Signatura PE", "SI AS 1086"),
        "title": metadata.get("Naslov PE", "Zbirka filmov"),
        "date": metadata.get("Čas nastanka PE", ""),
        "quantity": metadata.get("Količina PE", ""),
        "material_type": metadata.get("Zvrsti arhivskega gradiva", ""),
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    metadata.get("Historiat PE", ""),
                    metadata.get("Vsebina PE", ""),
                    metadata.get("Količina PE", ""),
                ]
                if value
            ),
            limit=900,
        ),
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": SFA_REPOSITORY_CODE,
        "archive_type": SFA_ARCHIVE_TYPE,
        "sfa_detail_url": SFA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": SFA_VAC_FUND_URL,
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
        "partner_site": SFA_VAC_FUND_URL,
        "platform": record.get("platform", SFA_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _collect_record_ids_from_public_neighbors(seed_ids=SFA_SEED_RECORD_IDS, max_records=SFA_MAX_SAMPLE_RECORDS):
    queue = deque(str(record_id) for record_id in seed_ids)
    seen = set()
    records = []
    pages = {}
    errors = []

    while queue and len(records) < max_records:
        record_id = queue.popleft()
        if record_id in seen:
            continue
        seen.add(record_id)
        url = SFA_VAC_RECORD_URL_TEMPLATE.format(record_id=record_id)
        try:
            response = _vac_get(url)
            response.raise_for_status()
            record = parse_sfa_vac_detail_page(response.text, response.url)
            if str(record.get("signature", "")).startswith("SI AS 1086/"):
                records.append(record)
                pages[record_id] = response
                for neighbor_id in record.get("neighbors", []):
                    if neighbor_id not in seen:
                        queue.append(neighbor_id)
        except Exception as exc:
            errors.append((url, str(exc)))
    return records, pages, errors


def collect_sfa_dataset():
    institutions = collect_sfa_institutions()
    institution = institutions[0]
    internal_pages = []
    catalog_errors = []

    for url, warning in [
        (SFA_HOME_URL, "Página oficial eslovena que confirma o Slovenski filmski arhiv."),
        (SFA_ENGLISH_URL, "Página oficial em inglês que confirma o Slovenian Film Archives."),
        (SFA_VAC_HOME_URL, "Entrada pública da Virtualna arhivska čitalnica."),
        (SFA_VAC_SEARCH_URL, "Formulário público de busca do VAČ; a chamada AJAX não é usada no MVP."),
    ]:
        try:
            response = _vac_get(url) if "vac.sjas.gov.si" in url else SESSION.get(url, timeout=(8, REQUEST_TIMEOUT))
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as exc:
            catalog_errors.append((url, str(exc)))
            internal_pages.append(_internal_page_row(institution, url, "erro", "", 0, 0, warning, str(exc)))

    try:
        fund_response = _vac_get(SFA_VAC_FUND_URL)
        fund_response.raise_for_status()
        fund_metadata = parse_sfa_vac_fund_page(fund_response.text, fund_response.url)
        internal_pages.append(
            _internal_page_row(
                institution,
                fund_response.url,
                "ok",
                fund_response.status_code,
                0,
                0,
                (
                    "Ficha pública do fundo SI AS 1086 usada para validar a coleção de filmes; "
                    f"{fund_metadata.get('quantity', '')}"
                ),
            )
        )
    except Exception as exc:
        catalog_errors.append((SFA_VAC_FUND_URL, str(exc)))
        internal_pages.append(_internal_page_row(institution, SFA_VAC_FUND_URL, "erro", "", 0, 0, "", str(exc)))

    records, record_pages, record_errors = _collect_record_ids_from_public_neighbors()
    catalog_errors.extend(record_errors)
    for record in records:
        response = record_pages.get(record["record_id"])
        internal_pages.append(
            _internal_page_row(
                institution,
                record["video_link"],
                "ok",
                response.status_code if response is not None else 200,
                1,
                0,
                "Ficha pública de filme no VAČ; metadados coletados sem pressupor player.",
            )
        )

    video_rows = [_record_to_video_row(institution, record) for record in records]
    summary = {
        **_base_row(institution),
        "partner_site": SFA_VAC_FUND_URL,
        "partner_domain": "vac.sjas.gov.si",
        "status": "ok" if video_rows else "sem_registros_materializados",
        "http_code": 200 if video_rows else "",
        "integrity_status": "integro" if video_rows else "rota_sem_amostra",
        "final_url": SFA_VAC_FUND_URL,
        "video_links_found_total": len(video_rows),
        "embedded_video_signals_total": 0,
        "candidate_internal_pages": len(internal_pages),
        "priority_review": "baixa" if video_rows else "alta",
        "warning": (
            "Corpus institucional incorporado por fichas públicas de metadados filmográficos no VAČ. "
            "A rota materializa registros do fundo SI AS 1086, mas não detecta player público nas fichas; "
            "por isso o corpus mede visibilidade/catalogação audiovisual, não streaming aberto."
        ),
        "error": "; ".join(f"{url}: {error}" for url, error in catalog_errors),
    }
    return institutions, [summary], video_rows, internal_pages


__all__ = [
    "SFA_MAX_SAMPLE_RECORDS",
    "SFA_SEED_RECORD_IDS",
    "collect_sfa_dataset",
    "collect_sfa_institutions",
    "parse_sfa_vac_detail_page",
    "parse_sfa_vac_fund_page",
]
