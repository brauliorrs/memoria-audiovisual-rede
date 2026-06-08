import json
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import ANF_EFG_PAGE_URL, ANF_EVENTBOOK_URL, ANF_OFFICIAL_URL, HEADERS, REQUEST_TIMEOUT
from .crawler import slugify
from .geography import country_to_continent, normalize_country


ANF_REPOSITORY_CODE = "RO-ANF"
ANF_ARCHIVE_TYPE = "Institutional film archive"
ANF_COUNTRY = normalize_country("Romania")
ANF_INSTITUTION_NAME = "Arhiva Nationala de Filme - Cinemateca Romana"
ANF_PLATFORM_LABEL = "Eventbook"
ANF_MAX_RECORDS = 8

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)


def collect_anf_institutions():
    return [
        {
            "institution": ANF_INSTITUTION_NAME,
            "slug": slugify(ANF_INSTITUTION_NAME),
            "country": ANF_COUNTRY,
            "continent": country_to_continent(ANF_COUNTRY),
            "repository_code": ANF_REPOSITORY_CODE,
            "archive_type": ANF_ARCHIVE_TYPE,
            "anf_detail_url": ANF_OFFICIAL_URL,
            "external_url": ANF_EVENTBOOK_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_anf_eventbook_collection_page(html_text, page_url=ANF_EVENTBOOK_URL, limit=ANF_MAX_RECORDS):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor["href"])
        if "/film/" not in href or "cinemateca-online" not in href:
            continue
        if href in seen:
            continue
        title = _clean_text(anchor.get_text(" ", strip=True))
        if not title or title.lower() in {"see more details", "online"}:
            continue
        seen.add(href)
        links.append({"title": title, "url": href})
        if len(links) >= limit:
            break
    return links


def _load_event_ld_json(soup):
    for script in soup.find_all("script", type="application/ld+json"):
        raw = script.string or script.get_text("", strip=True)
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("@type") == "Event":
            return payload
    return {}


def _event_title(payload, soup):
    name = payload.get("name") or ""
    title = re.sub(r"\s*-\s*Cinemateca Online\s*$", "", name).strip()
    if title:
        return title
    heading = soup.find("h1")
    return _clean_text(heading.get_text(" ", strip=True) if heading else "")


def _event_subject(description):
    first_line = next((line.strip() for line in str(description or "").splitlines() if line.strip()), "")
    if "/" not in first_line:
        return ""
    country_match = re.search(r"rom[aâ]nia\s*/\s*(.+)", first_line, re.I)
    if country_match:
        first_line = country_match.group(1)
    parts = [_clean_text(part) for part in first_line.split("/") if _clean_text(part)]
    candidates = [
        part
        for part in parts
        if not re.fullmatch(
            r"(rom[aâ]nia|romania|19\d{2}(?:-\d{4})?|\d+\s*[’']|a|n|a/n|color|alb[- ]negru|ag)",
            part,
            re.I,
        )
        and "versiune digital" not in part.lower()
    ]
    return " | ".join(candidates[:3])


def _event_year(description, payload):
    text = str(description or "")
    match = re.search(r"\b(19\d{2}|20\d{2})(?:-\d{4})?\b", text)
    if match:
        return match.group(0)
    start_date = str(payload.get("startDate", ""))
    return start_date[:4] if re.match(r"\d{4}", start_date) else ""


def _event_price(payload):
    offers = payload.get("offers") or {}
    if not isinstance(offers, dict):
        return ""
    price = offers.get("price")
    currency = offers.get("priceCurrency")
    if price in (None, ""):
        return ""
    return f"{price} {currency}".strip()


def parse_anf_eventbook_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    payload = _load_event_ld_json(soup)
    page_text = soup.get_text(" ", strip=True)
    description = _clean_text(payload.get("description") or page_text, limit=900)
    price = _event_price(payload)
    access_note = "Página pública de programação/streaming no Eventbook; sem player aberto detectado no HTML."
    if price:
        access_note = f"{access_note} Regime de acesso indicado: {price}, com compra/login."
    if "teritoriul României" in page_text or "teritoriul Rom" in page_text:
        access_note = f"{access_note} A própria página indica visualização restrita ao território romeno."
    return {
        "record_id": page_url.rstrip("/").rsplit("/", 1)[-1],
        "source_kind": "eventbook_cinemateca_online",
        "video_link": page_url,
        "platform": ANF_PLATFORM_LABEL,
        "title": _event_title(payload, soup),
        "subject": _event_subject(payload.get("description", "")),
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    "Cinemateca Online atribuída à Arhiva Națională de Filme.",
                    access_note,
                    description,
                ]
                if value
            ),
            limit=900,
        ),
        "date": _event_year(payload.get("description", ""), payload),
        "embedded": False,
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": ANF_REPOSITORY_CODE,
        "archive_type": ANF_ARCHIVE_TYPE,
        "anf_detail_url": ANF_OFFICIAL_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ANF_EVENTBOOK_URL,
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
        "partner_site": ANF_EVENTBOOK_URL,
        "platform": record.get("platform", ANF_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_anf_dataset():
    institutions = collect_anf_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    errors = []

    for url, warning in [
        (ANF_OFFICIAL_URL, "Site oficial informado pela FIAF/EFG; indisponibilidade não bloqueia a rota externa validada."),
        (ANF_EFG_PAGE_URL, "Página do European Film Gateway usada como evidência de cobertura agregadora, não como corpus institucional."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as exc:
            errors.append((url, str(exc)))
            internal_pages.append(_internal_page_row(institution, url, "erro", "", 0, 0, warning, str(exc)))

    try:
        response = _fetch(ANF_EVENTBOOK_URL)
        response.raise_for_status()
        candidates = parse_anf_eventbook_collection_page(response.text, response.url)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(candidates),
                0,
                "Lista pública Cinemateca Online no Eventbook; usada como superfície externa de acesso.",
            )
        )
        for candidate in candidates:
            detail_response = _fetch(candidate["url"])
            detail_response.raise_for_status()
            record = parse_anf_eventbook_detail_page(detail_response.text, detail_response.url)
            records.append(record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_response.url,
                    "ok",
                    detail_response.status_code,
                    1,
                    0,
                    "Página pública de filme/programa da Cinemateca Online; metadados coletados sem pressupor player aberto.",
                )
            )
    except Exception as exc:
        errors.append((ANF_EVENTBOOK_URL, str(exc)))
        internal_pages.append(_internal_page_row(institution, ANF_EVENTBOOK_URL, "erro", "", 0, 0, "", str(exc)))

    video_rows = [_record_to_video_row(institution, record) for record in records]
    summary = {
        **_base_row(institution),
        "partner_site": ANF_EVENTBOOK_URL,
        "partner_domain": "eventbook.ro",
        "status": "ok" if video_rows else "sem_registros_materializados",
        "http_code": 200 if video_rows else "",
        "integrity_status": "integro" if video_rows else "rota_sem_amostra",
        "final_url": ANF_EVENTBOOK_URL,
        "video_links_found_total": len(video_rows),
        "embedded_video_signals_total": 0,
        "candidate_internal_pages": len(internal_pages),
        "priority_review": "media",
        "warning": (
            "Corpus institucional incorporado por superfície externa Cinemateca Online/Eventbook. "
            "A rota oficial anf-cinemateca.ro não respondeu nesta rodada; a coleta não representa "
            "catálogo total da ANF e não baixa mídia."
        ),
        "error": "; ".join(f"{url}: {error}" for url, error in errors),
    }
    return institutions, [summary], video_rows, internal_pages


__all__ = [
    "ANF_MAX_RECORDS",
    "collect_anf_dataset",
    "collect_anf_institutions",
    "parse_anf_eventbook_collection_page",
    "parse_anf_eventbook_detail_page",
]
