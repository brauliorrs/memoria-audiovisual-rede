"""Staged collector for the public Gosfilmofond film catalogue.

Enumeration follows the catalogue's own public filter form. The collector uses
only the publicly advertised maximum page size and the explicitly allowed
/wp-admin/admin-ajax.php endpoint. It never scans film IDs and never downloads
audiovisual media.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    GOSFILMOFOND_AJAX_URL,
    GOSFILMOFOND_CATALOG_URL,
    GOSFILMOFOND_DETAIL_URL_TEMPLATE,
    GOSFILMOFOND_HOME_URL,
    HEADERS,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country
from .gosfilmofond_probe import (
    evaluate_robots,
    fetch_public_url,
    parse_ajax_response,
    parse_catalog_html,
    post_public_form,
)


GOSFILMOFOND_REPOSITORY_CODE = "RU-GOSFILMOFOND"
GOSFILMOFOND_ARCHIVE_TYPE = "National film archive"
GOSFILMOFOND_COUNTRY = normalize_country("Russia")
GOSFILMOFOND_INSTITUTION_NAME = "Gosfilmofond of Russia"
GOSFILMOFOND_PLATFORM_LABEL = "Gosfilmofond Film Catalogue"
GOSFILMOFOND_MAX_PUBLIC_PAGE_SIZE = 100
GOSFILMOFOND_MAX_PAGES_FAIL_CLOSED = 1000
GOSFILMOFOND_REQUEST_DELAY_SECONDS = 0.05

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _record_key_from_url(url):
    path = urlparse(str(url or "")).path.rstrip("/")
    if "/films/" not in path:
        return ""
    return path.rsplit("/", 1)[-1]


def _smallest_card_context(anchor):
    current = anchor.parent
    best = ""
    for _ in range(6):
        if current is None:
            break
        text = _clean_text(current.get_text(" ", strip=True), limit=2500)
        if text:
            best = text
        if (
            len(text) <= 1500
            and (
                re.search(r"\b(?:18|19|20)\d{2}\b", text)
                or re.search(r"режисс|страна|жанр|год", text, re.I)
            )
        ):
            return text
        current = current.parent
    return best


def parse_gosfilmofond_ajax_page(html_text, endpoint_url=GOSFILMOFOND_AJAX_URL):
    """Parse one public AJAX result page into stable film-card records."""
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        absolute = urljoin(endpoint_url, anchor.get("href", ""))
        key = _record_key_from_url(absolute)
        if not key or key in seen:
            continue
        parsed = urlparse(absolute)
        if not parsed.netloc.endswith("gosfilmofond.ru"):
            continue
        seen.add(key)
        title = _clean_text(anchor.get_text(" ", strip=True), limit=350)
        if not title:
            title = _clean_text(anchor.get("title"), limit=350)
        context = _smallest_card_context(anchor)
        year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", context)
        records.append(
            {
                "record_key": key,
                "page_url": GOSFILMOFOND_DETAIL_URL_TEMPLATE.format(record_key=key),
                "title": title or f"Film {key}",
                "date": year_match.group(1) if year_match else "",
                "card_context": context,
            }
        )
    meta = parse_ajax_response(html_text, endpoint_url)
    return records, meta


def collect_gosfilmofond_institutions():
    return [
        {
            "institution": GOSFILMOFOND_INSTITUTION_NAME,
            "slug": slugify(GOSFILMOFOND_INSTITUTION_NAME),
            "country": GOSFILMOFOND_COUNTRY,
            "continent": country_to_continent(GOSFILMOFOND_COUNTRY),
            "repository_code": GOSFILMOFOND_REPOSITORY_CODE,
            "archive_type": GOSFILMOFOND_ARCHIVE_TYPE,
            "gosfilmofond_detail_url": GOSFILMOFOND_HOME_URL,
            "external_url": GOSFILMOFOND_CATALOG_URL,
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
        "repository_code": GOSFILMOFOND_REPOSITORY_CODE,
        "archive_type": GOSFILMOFOND_ARCHIVE_TYPE,
        "gosfilmofond_detail_url": GOSFILMOFOND_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(
    institution,
    url,
    status,
    http_code="",
    count=0,
    warning="",
    error="",
):
    return {
        **_base_row(institution),
        "partner_site": GOSFILMOFOND_HOME_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": count,
        "embedded_signals": 0,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record, page_number):
    context = _clean_text(record.get("card_context", ""), limit=900)
    description = (
        "Ficha pública enumerada pelo catálogo oficial do Gosfilmofond. "
        "O permalink representa metadados cinematográficos e não implica "
        "streaming público ou licença de reprodução."
    )
    if context:
        description += f" Contexto público da ficha na listagem: {context}"
    return {
        **_base_row(institution),
        "partner_site": GOSFILMOFOND_HOME_URL,
        "platform": GOSFILMOFOND_PLATFORM_LABEL,
        "video_link": record["page_url"],
        "video_title": record.get("title", ""),
        "video_subject": f"catálogo de filmes; página AJAX {page_number}",
        "video_description": _clean_text(description, limit=1800),
        "video_published_at": record.get("date", ""),
    }


def _summary(
    institution,
    *,
    records_total,
    page_count,
    pages_total,
    pages_completed,
    duplicate_count,
    errors,
    integrity_status,
):
    warning = (
        "Enumeração do catálogo público via formulário oficial /films/ e endpoint "
        "/wp-admin/admin-ajax.php explicitamente permitido em robots.txt. "
        f"A interface pública declarou page_count={page_count}; a rodada observou "
        f"{pages_total} páginas e materializou {records_total} permalinks únicos. "
        "O corpus representa a superfície pública materializada nesta rodada, não "
        "o acervo físico total e não disponibilidade de streaming."
    )
    if duplicate_count:
        warning += f" Foram observadas {duplicate_count} duplicações entre páginas."
    return [
        {
            **_base_row(institution),
            "partner_site": GOSFILMOFOND_HOME_URL,
            "partner_domain": normalize_domain(GOSFILMOFOND_HOME_URL),
            "status": "ok" if records_total else "sem_registros",
            "http_code": 200 if records_total else "",
            "integrity_status": integrity_status,
            "final_url": GOSFILMOFOND_CATALOG_URL,
            "video_links_found_total": records_total,
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": pages_completed + 2,
            "priority_review": integrity_status != "integro",
            "warning": warning,
            "error": " | ".join(errors[:12]),
        }
    ]


def collect_gosfilmofond_dataset(
    *,
    session=None,
    sleep_fn=time.sleep,
    request_delay=GOSFILMOFOND_REQUEST_DELAY_SECONDS,
):
    """Enumerate the public catalogue, failing closed on coverage drift."""
    session = session or SESSION
    institutions = collect_gosfilmofond_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_key = {}
    record_page = {}
    duplicate_count = 0

    robots = evaluate_robots(
        session,
        [GOSFILMOFOND_CATALOG_URL, GOSFILMOFOND_AJAX_URL],
    )
    robot_map = {
        row["url"]: bool(row["allowed"])
        for row in robots.get("targets", [])
    }
    if not robot_map.get(GOSFILMOFOND_CATALOG_URL) or not robot_map.get(
        GOSFILMOFOND_AJAX_URL
    ):
        reason = (
            "robots_catalog_or_ajax_not_allowed:"
            + ",".join(
                f"{row['url']}={row.get('allowed')}:{row.get('reason')}"
                for row in robots.get("targets", [])
            )
        )
        internal_pages.append(
            _internal_page_row(
                institution,
                GOSFILMOFOND_CATALOG_URL,
                "bloqueado_robots",
                warning="Coleta interrompida antes da enumeração.",
                error=reason,
            )
        )
        return (
            institutions,
            _summary(
                institution,
                records_total=0,
                page_count=0,
                pages_total=0,
                pages_completed=0,
                duplicate_count=0,
                errors=[reason],
                integrity_status="instavel",
            ),
            [],
            internal_pages,
        )

    catalog_response = fetch_public_url(session, GOSFILMOFOND_CATALOG_URL)
    if catalog_response.status_code != 200 or catalog_response.error:
        error = catalog_response.error or f"http_{catalog_response.status_code}"
        internal_pages.append(
            _internal_page_row(
                institution,
                GOSFILMOFOND_CATALOG_URL,
                "erro",
                catalog_response.status_code or "",
                error=error,
            )
        )
        return (
            institutions,
            _summary(
                institution,
                records_total=0,
                page_count=0,
                pages_total=0,
                pages_completed=0,
                duplicate_count=0,
                errors=[error],
                integrity_status="instavel",
            ),
            [],
            internal_pages,
        )

    catalog = parse_catalog_html(
        catalog_response.text,
        catalog_response.final_url or GOSFILMOFOND_CATALOG_URL,
    )
    declared_sizes = [
        value
        for value in catalog.get("page_count_options", [])
        if 0 < value <= GOSFILMOFOND_MAX_PUBLIC_PAGE_SIZE
    ]
    if not declared_sizes:
        error = "public_page_count_options_missing"
        internal_pages.append(
            _internal_page_row(
                institution,
                GOSFILMOFOND_CATALOG_URL,
                "erro",
                catalog_response.status_code,
                error=error,
            )
        )
        return (
            institutions,
            _summary(
                institution,
                records_total=0,
                page_count=0,
                pages_total=0,
                pages_completed=0,
                duplicate_count=0,
                errors=[error],
                integrity_status="instavel",
            ),
            [],
            internal_pages,
        )
    page_count = max(declared_sizes)
    internal_pages.append(
        _internal_page_row(
            institution,
            catalog_response.final_url or GOSFILMOFOND_CATALOG_URL,
            "ok",
            catalog_response.status_code,
            warning=(
                "Catálogo público; tamanhos de página declarados="
                + ",".join(map(str, declared_sizes))
                + f"; selecionado={page_count}."
            ),
        )
    )

    max_page = None
    pages_completed = 0
    for page in range(1, GOSFILMOFOND_MAX_PAGES_FAIL_CLOSED + 1):
        payload = {
            "action": "filter_films",
            "paged": str(page),
            "order": "",
            "search": "",
            "page_count": str(page_count),
        }
        response = post_public_form(session, GOSFILMOFOND_AJAX_URL, payload)
        if response.status_code != 200 or response.error:
            error = response.error or f"http_{response.status_code}"
            errors.append(f"page_{page}:{error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{GOSFILMOFOND_AJAX_URL}#page={page}&page_count={page_count}",
                    "erro",
                    response.status_code or "",
                    error=error,
                )
            )
            break

        records, meta = parse_gosfilmofond_ajax_page(
            response.text,
            response.final_url or GOSFILMOFOND_AJAX_URL,
        )
        observed_max = meta.get("max_page_number")
        if page == 1:
            if (
                not observed_max
                or observed_max < 1
                or observed_max > GOSFILMOFOND_MAX_PAGES_FAIL_CLOSED
            ):
                error = f"invalid_observed_max_page:{observed_max}"
                errors.append(error)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        f"{GOSFILMOFOND_AJAX_URL}#page=1&page_count={page_count}",
                        "erro",
                        response.status_code,
                        len(records),
                        error=error,
                    )
                )
                break
            max_page = int(observed_max)
        elif observed_max and max_page and int(observed_max) != max_page:
            error = f"pagination_drift:page={page}:expected={max_page}:observed={observed_max}"
            errors.append(error)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{GOSFILMOFOND_AJAX_URL}#page={page}&page_count={page_count}",
                    "erro",
                    response.status_code,
                    len(records),
                    error=error,
                )
            )
            break

        if not records:
            error = f"empty_required_page:{page}"
            errors.append(error)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{GOSFILMOFOND_AJAX_URL}#page={page}&page_count={page_count}",
                    "erro",
                    response.status_code,
                    0,
                    error=error,
                )
            )
            break
        if max_page and page < max_page and len(records) != page_count:
            error = (
                f"short_intermediate_page:{page}:"
                f"expected={page_count}:observed={len(records)}"
            )
            errors.append(error)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{GOSFILMOFOND_AJAX_URL}#page={page}&page_count={page_count}",
                    "erro",
                    response.status_code,
                    len(records),
                    error=error,
                )
            )
            break

        page_duplicates = 0
        for record in records:
            key = record["record_key"]
            if key in records_by_key:
                duplicate_count += 1
                page_duplicates += 1
                continue
            records_by_key[key] = record
            record_page[key] = page

        pages_completed += 1
        internal_pages.append(
            _internal_page_row(
                institution,
                f"{GOSFILMOFOND_AJAX_URL}#page={page}&page_count={page_count}",
                "ok",
                response.status_code,
                len(records),
                warning=(
                    f"POST público action=filter_films; página={page}; "
                    f"page_count={page_count}; duplicados={page_duplicates}."
                ),
            )
        )
        if max_page and page >= max_page:
            break
        if request_delay:
            sleep_fn(request_delay)

    if max_page is None:
        errors.append("pagination_not_established")
    elif pages_completed != max_page:
        errors.append(
            f"incomplete_pages:expected={max_page}:completed={pages_completed}"
        )
    if duplicate_count:
        errors.append(f"cross_page_duplicates:{duplicate_count}")

    records_total = len(records_by_key)
    if max_page:
        minimum_expected = (max_page - 1) * page_count + 1
        maximum_expected = max_page * page_count
        if not (minimum_expected <= records_total <= maximum_expected):
            errors.append(
                "record_count_outside_page_bounds:"
                f"{records_total}:expected={minimum_expected}-{maximum_expected}"
            )

    integrity_status = "integro" if not errors and records_total else "instavel"
    video_links = [
        _record_to_video_row(
            institution,
            records_by_key[key],
            record_page[key],
        )
        for key in records_by_key
    ]

    return (
        institutions,
        _summary(
            institution,
            records_total=records_total,
            page_count=page_count,
            pages_total=max_page or 0,
            pages_completed=pages_completed,
            duplicate_count=duplicate_count,
            errors=errors,
            integrity_status=integrity_status,
        ),
        video_links,
        internal_pages,
    )


__all__ = [
    "GOSFILMOFOND_ARCHIVE_TYPE",
    "GOSFILMOFOND_COUNTRY",
    "GOSFILMOFOND_INSTITUTION_NAME",
    "GOSFILMOFOND_MAX_PAGES_FAIL_CLOSED",
    "GOSFILMOFOND_MAX_PUBLIC_PAGE_SIZE",
    "GOSFILMOFOND_PLATFORM_LABEL",
    "GOSFILMOFOND_REPOSITORY_CODE",
    "collect_gosfilmofond_dataset",
    "collect_gosfilmofond_institutions",
    "parse_gosfilmofond_ajax_page",
]
