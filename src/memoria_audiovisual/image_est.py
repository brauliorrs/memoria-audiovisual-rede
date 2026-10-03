from __future__ import annotations

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country
from .image_est_probe import (
    CRAWLER_TOKEN,
    IMAGE_EST_HOME_URL,
    IMAGE_EST_ROBOTS_URL,
    ProbeResponse,
    fetch_public_url,
    parse_detail_html,
    robots_allowed,
)


IMAGE_EST_SITEMAP_URL = "https://www.image-est.fr/sitemap.xml"
IMAGE_EST_INSTITUTION_NAME = "Image'Est"
IMAGE_EST_REPOSITORY_CODE = "FR-IMAGE-EST"
IMAGE_EST_ARCHIVE_TYPE = "Regional audiovisual heritage archive"
IMAGE_EST_COUNTRY = normalize_country("France")
IMAGE_EST_PLATFORM_LABEL = "Image'Est - Patrimoine"
IMAGE_EST_MAX_DETAIL_PAGES = 24
IMAGE_EST_AUDIOVISUAL_TYPE_CODES = frozenset({"1", "3"})
IMAGE_EST_NON_AUDIOVISUAL_TYPE_CODES = frozenset({"2"})
IMAGE_EST_EXPECTED_TYPE_CODES = (
    IMAGE_EST_AUDIOVISUAL_TYPE_CODES | IMAGE_EST_NON_AUDIOVISUAL_TYPE_CODES
)

_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_TYPED_DETAIL_PATH_RE = re.compile(
    r"/fiche-documentaire-[^?#]+-1284-[^/?#]+-(\d+)-0\.html$",
    re.I,
)
_DETAIL_PATH_RE = re.compile(r"/fiche-documentaire-[^/?#]+\.html$", re.I)
_SITEMAP_DIRECTIVE_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "User-Agent": f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-collector)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def parse_image_est_sitemap(xml_text):
    """Return every typed documentary permalink grouped by Image'Est type code."""
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    typed_urls: dict[str, set[str]] = {}
    untyped_details: set[str] = set()
    duplicates: set[str] = set()
    seen: set[str] = set()

    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme.lower() != "https" or parsed.netloc.lower() != "www.image-est.fr":
            continue
        if not _DETAIL_PATH_RE.match(parsed.path):
            continue
        if url in seen:
            duplicates.add(url)
            continue
        seen.add(url)

        match = _TYPED_DETAIL_PATH_RE.match(parsed.path)
        if not match:
            untyped_details.add(url)
            continue
        typed_urls.setdefault(match.group(1), set()).add(url)

    return {
        "typed_urls": {
            code: sorted(values)
            for code, values in sorted(typed_urls.items())
        },
        "typed_counts": {
            code: len(values)
            for code, values in sorted(typed_urls.items())
        },
        "untyped_details": sorted(untyped_details),
        "duplicates": sorted(duplicates),
        "detail_total": len(seen),
    }


def _valid_robots_payload(response: ProbeResponse):
    if response.error:
        return False, "robots_unreachable", ""
    if response.status_code != 200:
        return False, f"robots_http_{response.status_code}", ""
    text = response.text or ""
    stripped = text.strip()
    if not stripped or "<html" in stripped.lower():
        return False, "robots_invalid_payload", ""
    return True, "robots_evaluated_rfc9309", text


def _fetch_robots(session=SESSION):
    response = fetch_public_url(session, IMAGE_EST_ROBOTS_URL)
    valid, status, text = _valid_robots_payload(response)
    if not valid:
        return False, status, ""
    declared = set(_SITEMAP_DIRECTIVE_RE.findall(text))
    if IMAGE_EST_SITEMAP_URL not in declared:
        return False, "required_sitemap_not_declared", text
    if not robots_allowed(text, CRAWLER_TOKEN, IMAGE_EST_SITEMAP_URL):
        return False, "sitemap_blocked_by_robots", text
    return True, status, text


def _fetch_allowed(session, url, robots_text):
    return fetch_public_url(
        session,
        url,
        robots_text=robots_text,
    )


def _label_value(soup, label):
    label_re = re.compile(rf"^{re.escape(label)}\s*:?\s*", re.I)
    for node in soup.find_all(["dt", "th", "strong", "b", "p", "div", "span", "li"]):
        raw = _clean_text(node.get_text(" ", strip=True), limit=1200)
        if not label_re.search(raw):
            continue
        remainder = label_re.sub("", raw, count=1).strip(" :-")
        if remainder:
            return _clean_text(remainder, limit=500)
        sibling = node.find_next_sibling()
        if sibling is not None:
            value = _clean_text(sibling.get_text(" ", strip=True), limit=500)
            if value:
                return value
    return ""


def parse_image_est_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    heading = soup.find("h1") or soup.find("h2")
    semantics = parse_detail_html(html_text, page_url)
    return {
        "page_url": page_url,
        "title": _clean_text(
            heading.get_text(" ", strip=True) if heading else "",
            limit=500,
        ),
        "date": _label_value(soup, "Année"),
        "duration": _label_value(soup, "Durée"),
        "format": _label_value(soup, "Format"),
        "sound": _label_value(soup, "Son"),
        "fonds": _label_value(soup, "Fonds"),
        "film_semantics_confirmed": bool(
            semantics.get("film_semantics_confirmed")
        ),
        "embedded_player_present": bool(
            semantics.get("embedded_player_present")
        ),
    }


def collect_image_est_institutions():
    return [
        {
            "institution": IMAGE_EST_INSTITUTION_NAME,
            "slug": slugify(IMAGE_EST_INSTITUTION_NAME),
            "country": IMAGE_EST_COUNTRY,
            "continent": country_to_continent(IMAGE_EST_COUNTRY),
            "repository_code": IMAGE_EST_REPOSITORY_CODE,
            "archive_type": IMAGE_EST_ARCHIVE_TYPE,
            "image_est_detail_url": IMAGE_EST_HOME_URL,
            "external_url": IMAGE_EST_HOME_URL,
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
        "repository_code": IMAGE_EST_REPOSITORY_CODE,
        "archive_type": IMAGE_EST_ARCHIVE_TYPE,
        "image_est_detail_url": IMAGE_EST_HOME_URL,
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
        "partner_site": IMAGE_EST_HOME_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": count,
        "embedded_signals": 0,
        "warning": warning,
        "error": error,
    }


def _record_to_video_row(institution, record):
    metadata_parts = []
    for key, label in (
        ("type_code", "Image'Est type"),
        ("duration", "Durée"),
        ("format", "Format"),
        ("sound", "Son"),
        ("fonds", "Fonds"),
    ):
        if record.get(key):
            metadata_parts.append(f"{label}: {record[key]}")
    description = (
        "Public audiovisual documentary record enumerated from the Image'Est "
        "robots-declared sitemap. MAR materializes the public metadata permalink "
        "only and does not download or redistribute audiovisual media."
    )
    if metadata_parts:
        description += " " + "; ".join(metadata_parts) + "."
    return {
        **_base_row(institution),
        "partner_site": IMAGE_EST_HOME_URL,
        "platform": IMAGE_EST_PLATFORM_LABEL,
        "video_link": record["page_url"],
        "video_title": record.get("title", ""),
        "video_subject": record.get("fonds") or "Image'Est audiovisual record",
        "video_description": description,
        "video_published_at": record.get("date", ""),
    }


def _classification_samples(typed_urls):
    samples = {}
    for type_code, urls in sorted(typed_urls.items()):
        samples[type_code] = list(urls[:2])
    return samples


def collect_image_est_dataset(
    *,
    session=SESSION,
    robots_loader=_fetch_robots,
    fetch_allowed=_fetch_allowed,
):
    institutions = collect_image_est_institutions()
    institution = institutions[0]
    internal_pages = []
    fatal_errors = []
    detail_warnings = []

    robots_ok, robots_status, robots_text = robots_loader(session)
    if not robots_ok:
        internal_pages.append(
            _internal_page_row(
                institution,
                IMAGE_EST_SITEMAP_URL,
                "bloqueado_robots",
                warning="Enumeração abortada antes do sitemap.",
                error=robots_status,
            )
        )
        summary = [
            {
                **_base_row(institution),
                "partner_site": IMAGE_EST_HOME_URL,
                "partner_domain": normalize_domain(IMAGE_EST_HOME_URL),
                "status": "sem_registros",
                "http_code": "",
                "integrity_status": "instavel",
                "final_url": IMAGE_EST_SITEMAP_URL,
                "video_links_found_total": 0,
                "embedded_video_signals_total": 0,
                "candidate_internal_pages": 1,
                "priority_review": True,
                "warning": (
                    "Image'Est confirmado, mas o sitemap não pôde ser usado "
                    "sob a política fail-closed de robots."
                ),
                "error": robots_status,
            }
        ]
        return institutions, summary, [], internal_pages

    sitemap_response = fetch_allowed(
        session,
        IMAGE_EST_SITEMAP_URL,
        robots_text,
    )
    if sitemap_response.error or sitemap_response.status_code != 200:
        fatal_errors.append(
            f"sitemap: {sitemap_response.error or sitemap_response.status_code}"
        )
        parsed = {
            "typed_urls": {},
            "typed_counts": {},
            "untyped_details": [],
            "duplicates": [],
            "detail_total": 0,
        }
    else:
        parsed = parse_image_est_sitemap(sitemap_response.text)

    internal_pages.append(
        _internal_page_row(
            institution,
            sitemap_response.final_url or IMAGE_EST_SITEMAP_URL,
            "ok" if not fatal_errors else "erro",
            sitemap_response.status_code or "",
            count=parsed["detail_total"],
            warning=(
                "Sitemap público declarado por robots; "
                f"tipos={parsed['typed_counts']}; robots={robots_status}."
            ),
            error=" | ".join(fatal_errors),
        )
    )

    observed_codes = set(parsed["typed_urls"])
    unexpected_codes = observed_codes - IMAGE_EST_EXPECTED_TYPE_CODES
    missing_codes = IMAGE_EST_EXPECTED_TYPE_CODES - observed_codes
    if unexpected_codes:
        fatal_errors.append(
            "unexpected_type_codes=" + ",".join(sorted(unexpected_codes))
        )
    if missing_codes:
        fatal_errors.append(
            "missing_type_codes=" + ",".join(sorted(missing_codes))
        )
    if parsed["untyped_details"]:
        fatal_errors.append(
            f"untyped_details={len(parsed['untyped_details'])}"
        )
    if parsed["duplicates"]:
        fatal_errors.append(
            f"duplicate_sitemap_urls={len(parsed['duplicates'])}"
        )

    classifications = {}
    for type_code, sample_urls in _classification_samples(
        parsed["typed_urls"]
    ).items():
        sample_rows = []
        for detail_url in sample_urls:
            if not robots_allowed(robots_text, CRAWLER_TOKEN, detail_url):
                fatal_errors.append(
                    f"type_{type_code}_sample_blocked_by_robots"
                )
                sample_rows.append(
                    {"url": detail_url, "film_semantics_confirmed": None}
                )
                continue
            response = fetch_allowed(session, detail_url, robots_text)
            if response.error or response.status_code != 200:
                fatal_errors.append(
                    f"type_{type_code}_sample_fetch_failed"
                )
                sample_rows.append(
                    {"url": detail_url, "film_semantics_confirmed": None}
                )
                continue
            detail = parse_image_est_detail_page(
                response.text,
                response.final_url or detail_url,
            )
            sample_rows.append(detail)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.final_url or detail_url,
                    "ok",
                    response.status_code,
                    count=1,
                    warning=(
                        "Amostra semântica determinística para validar "
                        f"Image'Est type={type_code}."
                    ),
                )
            )

        complete = (
            len(sample_rows) == 2
            and all(
                row.get("film_semantics_confirmed") is not None
                for row in sample_rows
            )
        )
        audiovisual = (
            complete
            and all(
                row.get("film_semantics_confirmed")
                for row in sample_rows
            )
        )
        non_audiovisual = (
            complete
            and all(
                not row.get("film_semantics_confirmed")
                for row in sample_rows
            )
        )
        classification = (
            "audiovisual"
            if audiovisual
            else "non_audiovisual"
            if non_audiovisual
            else "ambiguous"
        )
        classifications[type_code] = classification

        expected = (
            "audiovisual"
            if type_code in IMAGE_EST_AUDIOVISUAL_TYPE_CODES
            else "non_audiovisual"
        )
        if classification != expected:
            fatal_errors.append(
                f"type_{type_code}_semantic_drift={classification}"
            )

        internal_pages.append(
            _internal_page_row(
                institution,
                f"{IMAGE_EST_SITEMAP_URL}#type={type_code}",
                "ok" if classification == expected else "erro",
                sitemap_response.status_code or "",
                count=parsed["typed_counts"].get(type_code, 0),
                warning=(
                    f"Classificação estrutural type={type_code}: "
                    f"{classification}; esperado={expected}."
                ),
                error="" if classification == expected else "semantic_drift",
            )
        )

    records = []
    for type_code in sorted(IMAGE_EST_AUDIOVISUAL_TYPE_CODES):
        for page_url in parsed["typed_urls"].get(type_code, []):
            records.append(
                {
                    "page_url": page_url,
                    "type_code": type_code,
                    "title": (
                        page_url.rsplit("/", 1)[-1]
                        .removeprefix("fiche-documentaire-")
                        .rsplit("-1284-", 1)[0]
                        .replace("-", " ")
                    ),
                    "date": "",
                    "duration": "",
                    "format": "",
                    "sound": "",
                    "fonds": "",
                }
            )
    records.sort(key=lambda row: row["page_url"])

    detail_candidates = []
    for type_code in sorted(IMAGE_EST_AUDIOVISUAL_TYPE_CODES):
        detail_candidates.extend(
            [
                row
                for row in records
                if row["type_code"] == type_code
            ][: IMAGE_EST_MAX_DETAIL_PAGES // 2]
        )
    remaining = IMAGE_EST_MAX_DETAIL_PAGES - len(detail_candidates)
    if remaining > 0:
        chosen = {row["page_url"] for row in detail_candidates}
        detail_candidates.extend(
            [row for row in records if row["page_url"] not in chosen][:remaining]
        )

    for record in detail_candidates:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, record["page_url"]):
            detail_warnings.append(
                f"{record['page_url']}: robots blocked"
            )
            continue
        response = fetch_allowed(session, record["page_url"], robots_text)
        if response.error or response.status_code != 200:
            detail_warnings.append(
                f"{record['page_url']}: "
                f"{response.error or response.status_code}"
            )
            continue
        detail = parse_image_est_detail_page(
            response.text,
            response.final_url or record["page_url"],
        )
        if not detail["film_semantics_confirmed"]:
            fatal_errors.append(
                f"enriched_audiovisual_record_lost_semantics={record['page_url']}"
            )
            continue
        for key in ("title", "date", "duration", "format", "sound", "fonds"):
            if detail.get(key):
                record[key] = detail[key]
        internal_pages.append(
            _internal_page_row(
                institution,
                response.final_url or record["page_url"],
                "ok",
                response.status_code,
                count=1,
                warning=(
                    "Ficha audiovisual pública enriquecida deterministicamente; "
                    f"type={record['type_code']}."
                ),
            )
        )

    links = [_record_to_video_row(institution, record) for record in records]
    unique_links = {row["video_link"] for row in links}
    if len(unique_links) != len(links):
        fatal_errors.append("duplicate_materialized_permalinks")

    expected_total = sum(
        parsed["typed_counts"].get(type_code, 0)
        for type_code in IMAGE_EST_AUDIOVISUAL_TYPE_CODES
    )
    if len(links) != expected_total:
        fatal_errors.append(
            f"materialized_total_mismatch={len(links)}!={expected_total}"
        )

    integrity = (
        "integro"
        if links
        and not fatal_errors
        and set(classifications) == IMAGE_EST_EXPECTED_TYPE_CODES
        else "instavel"
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": IMAGE_EST_HOME_URL,
            "partner_domain": normalize_domain(IMAGE_EST_HOME_URL),
            "status": "ok" if links else "sem_registros",
            "http_code": 200 if links else "",
            "integrity_status": integrity,
            "final_url": IMAGE_EST_SITEMAP_URL,
            "video_links_found_total": len(links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": integrity != "integro",
            "warning": _clean_text(
                "Snapshot Image'Est enumerado pelo sitemap público declarado em "
                "robots.txt. Apenas os tipos 1 e 3, validados como audiovisuais, "
                f"foram materializados; tipo 2 foi excluído. Contagens da rodada: "
                f"{parsed['typed_counts']}. Total audiovisual={len(links)}. "
                "A rota AJAX /js/ permanece explicitamente fora de escopo por robots. "
                "A declaração institucional de acervo físico não é denominador de "
                "completude web. Nenhuma mídia foi baixada. "
                f"Enriquecimento determinístico limitado a "
                f"{IMAGE_EST_MAX_DETAIL_PAGES} fichas; "
                f"avisos não fatais={len(detail_warnings)}."
            ),
            "error": " | ".join(fatal_errors[:20]),
        }
    ]
    return institutions, summary, links, internal_pages


__all__ = [
    "IMAGE_EST_AUDIOVISUAL_TYPE_CODES",
    "IMAGE_EST_EXPECTED_TYPE_CODES",
    "IMAGE_EST_MAX_DETAIL_PAGES",
    "IMAGE_EST_SITEMAP_URL",
    "collect_image_est_dataset",
    "collect_image_est_institutions",
    "parse_image_est_detail_page",
    "parse_image_est_sitemap",
]
