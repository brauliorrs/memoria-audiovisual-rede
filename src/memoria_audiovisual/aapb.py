import re
import time
from urllib.parse import quote
from xml.etree import ElementTree as ET

import requests

from .config import (
    AAPB_API_URL_TEMPLATE,
    AAPB_FAQ_URL,
    AAPB_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
)
from .crawler import normalize_domain
from .geography import country_to_continent, normalize_country


AAPB_REPOSITORY_CODE = "US-AAPB"
AAPB_ARCHIVE_TYPE = "National audiovisual aggregator"
AAPB_COUNTRY = normalize_country("United States")
AAPB_INSTITUTION_NAME = "American Archive of Public Broadcasting"
AAPB_PLATFORM_LABEL = "American Archive of Public Broadcasting"
AAPB_SLUG = "american-archive-public-broadcasting"
AAPB_QUERY_TERMS = ("video", "film", "television")
AAPB_MAX_RECORDS_PER_TERM = 12
PBCORE_NS = {"pb": "http://www.pbcore.org/PBCore/PBCoreNamespace.html"}

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def collect_aapb_institutions():
    return [
        {
            "institution": AAPB_INSTITUTION_NAME,
            "slug": AAPB_SLUG,
            "country": AAPB_COUNTRY,
            "continent": country_to_continent(AAPB_COUNTRY),
            "repository_code": AAPB_REPOSITORY_CODE,
            "archive_type": AAPB_ARCHIVE_TYPE,
            "aapb_detail_url": AAPB_FAQ_URL,
            "external_url": AAPB_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _pbcore_texts(root, path):
    return [
        _clean_text(element.text)
        for element in root.findall(path, PBCORE_NS)
        if _clean_text(element.text)
    ]


def _parse_pbcore_xml(xml_text):
    try:
        root = ET.fromstring(xml_text or "")
    except ET.ParseError:
        return {}

    return {
        "description": _clean_text(" | ".join(_pbcore_texts(root, "pb:pbcoreDescription")), limit=900),
        "subjects": _clean_text("; ".join(_pbcore_texts(root, "pb:pbcoreSubject")), limit=500),
        "creators": _clean_text("; ".join(_pbcore_texts(root, "pb:pbcoreCreator/pb:creator")), limit=300),
        "publishers": _clean_text("; ".join(_pbcore_texts(root, "pb:pbcorePublisher/pb:publisher")), limit=300),
        "date": (_pbcore_texts(root, "pb:pbcoreAssetDate") or [""])[0],
        "media_types": _clean_text("; ".join(_pbcore_texts(root, ".//pb:instantiationMediaType")), limit=300),
        "duration": (_pbcore_texts(root, ".//pb:instantiationDuration") or [""])[0],
    }


def _has_moving_image_evidence(record):
    media_types = str(record.get("media_types", "")).lower()
    return any(token in media_types for token in ("moving image", "video", "film", "television"))


def parse_aapb_api_payload(payload, query):
    response = payload.get("response", {}) if isinstance(payload, dict) else {}
    records = []
    for doc in response.get("docs", []):
        record_id = str(doc.get("id", "")).strip()
        if not record_id:
            continue
        pbcore = _parse_pbcore_xml(doc.get("xml", ""))
        if not _has_moving_image_evidence(pbcore):
            continue
        records.append(
            {
                "record_id": record_id,
                "title": _clean_text(doc.get("title", "")),
                "aapb_url": f"{AAPB_HOME_URL.rstrip('/')}/catalog/{record_id}",
                "query": query,
                "timestamp": doc.get("timestamp", ""),
                **pbcore,
            }
        )
    return records, int(response.get("numFound", 0) or 0)


def _fetch_api_page(query):
    api_url = AAPB_API_URL_TEMPLATE.format(query=quote(query), rows=AAPB_MAX_RECORDS_PER_TERM)
    response = SESSION.get(api_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    return response, api_url


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": AAPB_REPOSITORY_CODE,
        "archive_type": AAPB_ARCHIVE_TYPE,
        "aapb_detail_url": AAPB_FAQ_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _record_to_video_row(institution, record):
    media_note = f"; mídia PBCore: {record.get('media_types')}" if record.get("media_types") else ""
    duration_note = f"; duração: {record.get('duration')}" if record.get("duration") else ""
    creator_note = f"; criador: {record.get('creators')}" if record.get("creators") else ""
    publisher_note = f"; publicador: {record.get('publishers')}" if record.get("publishers") else ""
    description_note = f"; descrição: {record.get('description')}" if record.get("description") else ""
    return {
        **_base_row(institution),
        "partner_site": record.get("publishers") or record.get("creators") or AAPB_PLATFORM_LABEL,
        "platform": AAPB_PLATFORM_LABEL,
        "video_link": record.get("aapb_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subjects") or record.get("query", ""),
        "video_description": _clean_text(
            f"registro PBCore AAPB {record.get('record_id', '')}{media_note}"
            f"{duration_note}{creator_note}{publisher_note}{description_note}",
            limit=900,
        ),
        "video_published_at": record.get("date", ""),
    }


def collect_aapb_dataset():
    institutions = collect_aapb_institutions()
    institution = institutions[0]
    discovered_records = {}
    internal_pages = []
    search_result_total = 0

    for index, query in enumerate(AAPB_QUERY_TERMS):
        if index:
            time.sleep(max(SLEEP_BETWEEN_REQUESTS, 1))
        try:
            response, api_url = _fetch_api_page(query)
            records, result_count = [], 0
            status = "ok" if response.status_code < 400 else "erro"
            error = ""
            if response.status_code == 200:
                payload = response.json()
                records, result_count = parse_aapb_api_payload(payload, query)
                search_result_total += result_count
                for record in records:
                    discovered_records.setdefault(record["record_id"], record)
            else:
                error = f"HTTP {response.status_code}"

            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": AAPB_HOME_URL,
                    "internal_page": response.url if response is not None else api_url,
                    "status": status,
                    "http_code": response.status_code if response is not None else "",
                    "video_links_found": len(records),
                    "embedded_signals": result_count,
                    "warning": f"API pública experimental do AAPB pelo termo: {query}.",
                    "error": error,
                }
            )
        except Exception as error:
            internal_pages.append(
                {
                    **_base_row(institution),
                    "partner_site": AAPB_HOME_URL,
                    "internal_page": AAPB_API_URL_TEMPLATE.format(query=quote(query), rows=AAPB_MAX_RECORDS_PER_TERM),
                    "status": "erro",
                    "http_code": "",
                    "video_links_found": 0,
                    "embedded_signals": 0,
                    "warning": "",
                    "error": str(error),
                }
            )

    video_links = [_record_to_video_row(institution, record) for record in discovered_records.values()]
    summary_status = "ok" if any(page["status"] == "ok" for page in internal_pages) else "erro"
    summary_error = "; ".join(sorted({str(page["error"]) for page in internal_pages if page.get("error")}))
    summary_warning = (
        "Corpus nacional audiovisual incorporado por rota API JSON/PBCore. A busca pública em HTML "
        "pode exigir navegação, mas a API permite amostra reprodutível e leve para o MVP."
    )

    summary = [
        {
            **_base_row(institution),
            "partner_site": AAPB_HOME_URL,
            "partner_domain": normalize_domain(AAPB_HOME_URL),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "instavel",
            "final_url": AAPB_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": search_result_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "media",
            "warning": f"{summary_warning} Resultados brutos sinalizados pela API: {search_result_total}.",
            "error": summary_error,
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "AAPB_QUERY_TERMS",
    "collect_aapb_dataset",
    "collect_aapb_institutions",
    "parse_aapb_api_payload",
]
