from __future__ import annotations

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    IWM_FILM_HOME_URL,
    IWM_FILM_SITEMAP_INDEX_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country
from .iwm_film_probe import (
    CRAWLER_TOKEN,
    IWM_FILM_ROBOTS_URL,
    ProbeResponse,
    fetch_public_url,
    parse_record_html,
    robots_allowed,
)


IWM_FILM_INSTITUTION_NAME = "Imperial War Museums"
IWM_FILM_REPOSITORY_CODE = "GB-IWM-FILM"
IWM_FILM_ARCHIVE_TYPE = "National museum film archive"
IWM_FILM_COUNTRY = normalize_country("United Kingdom")
IWM_FILM_PLATFORM_LABEL = "IWM Film"
IWM_FILM_MAX_DETAIL_PAGES = 24

_ALLOWED_HOST = "film.iwmcollections.org.uk"
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_RECORD_PATH_RE = re.compile(r"^/record/(\d+)/?$", re.I)
_RECORD_SITEMAP_RE = re.compile(
    r"^https://film\.iwmcollections\.org\.uk/"
    r"instance/sitemaps/sitemap-records(?:-\d+)?\.xml$",
    re.I,
)
_SITEMAP_DIRECTIVE_RE = re.compile(r"(?im)^\s*Sitemap:\s*(\S+)\s*$")
_DETAIL_LABELS = (
    "Film Number",
    "Production Date",
    "Production Country",
    "Sound",
    "Physical Characteristics",
    "Technical Details",
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "User-Agent": f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-collector)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def parse_iwm_sitemap_index(xml_text):
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    return sorted({url for url in urls if _RECORD_SITEMAP_RE.match(url)})


def parse_iwm_record_sitemap(xml_text):
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    records = []
    duplicates = set()
    rejected = []
    seen = set()
    for url in urls:
        parsed = urlparse(url)
        valid_origin = (
            parsed.scheme.lower() == "https"
            and parsed.netloc.lower() == _ALLOWED_HOST
        )
        valid_path = bool(_RECORD_PATH_RE.match(parsed.path))
        clean_permalink = not (parsed.params or parsed.query or parsed.fragment)
        if not (valid_origin and valid_path and clean_permalink):
            rejected.append(url)
            continue
        canonical = f"https://{_ALLOWED_HOST}{parsed.path.rstrip('/')}"
        if canonical in seen:
            duplicates.add(canonical)
            continue
        seen.add(canonical)
        records.append(canonical)
    return {
        "record_urls": sorted(records),
        "duplicates": sorted(duplicates),
        "rejected_urls": sorted(set(rejected)),
        "rejected_location_count": len(rejected),
        "url_count": len(urls),
        "record_count": len(records),
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
    response = fetch_public_url(session, IWM_FILM_ROBOTS_URL)
    valid, status, text = _valid_robots_payload(response)
    if not valid:
        return False, status, ""
    declared = set(_SITEMAP_DIRECTIVE_RE.findall(text))
    if IWM_FILM_SITEMAP_INDEX_URL not in declared:
        return False, "required_sitemap_index_not_declared", text
    if not robots_allowed(text, CRAWLER_TOKEN, IWM_FILM_SITEMAP_INDEX_URL):
        return False, "sitemap_index_blocked_by_robots", text
    return True, status, text


def _fetch_allowed(session, url, robots_text):
    return fetch_public_url(session, url, robots_text=robots_text)


def _label_value(soup, label):
    label_re = re.compile(rf"^{re.escape(label)}\s*:?\s*", re.I)
    for node in soup.find_all(["dt", "th", "strong", "b", "p", "div", "span", "li"]):
        raw = _clean_text(node.get_text(" ", strip=True), limit=1600)
        if not label_re.search(raw):
            continue
        remainder = label_re.sub("", raw, count=1).strip(" :-")
        if remainder:
            return _clean_text(remainder, limit=700)
        sibling = node.find_next_sibling()
        if sibling is not None:
            value = _clean_text(sibling.get_text(" ", strip=True), limit=700)
            if value:
                return value
    return ""


def parse_iwm_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    semantics = parse_record_html(html_text, page_url)
    values = {label: _label_value(soup, label) for label in _DETAIL_LABELS}
    return {
        "page_url": page_url,
        "title": semantics.get("title", ""),
        "film_number": values["Film Number"],
        "digitised": semantics.get("digitised", ""),
        "date": values["Production Date"],
        "production_country": values["Production Country"],
        "sound": values["Sound"],
        "physical_characteristics": values["Physical Characteristics"],
        "technical_details": values["Technical Details"],
        "media_markers": semantics.get("media_markers", []),
        "film_semantics_confirmed": bool(
            semantics.get("film_semantics_confirmed")
        ),
    }


def collect_iwm_film_institutions():
    return [
        {
            "institution": IWM_FILM_INSTITUTION_NAME,
            "slug": slugify(IWM_FILM_INSTITUTION_NAME),
            "country": IWM_FILM_COUNTRY,
            "continent": country_to_continent(IWM_FILM_COUNTRY),
            "repository_code": IWM_FILM_REPOSITORY_CODE,
            "archive_type": IWM_FILM_ARCHIVE_TYPE,
            "iwm_film_detail_url": IWM_FILM_HOME_URL,
            "external_url": IWM_FILM_HOME_URL,
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
        "repository_code": IWM_FILM_REPOSITORY_CODE,
        "archive_type": IWM_FILM_ARCHIVE_TYPE,
        "iwm_film_detail_url": IWM_FILM_HOME_URL,
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
        "partner_site": IWM_FILM_HOME_URL,
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
        ("film_number", "Film Number"),
        ("digitised", "Digitised"),
        ("production_country", "Production Country"),
        ("sound", "Sound"),
        ("physical_characteristics", "Physical Characteristics"),
        ("technical_details", "Technical Details"),
    ):
        if record.get(key):
            metadata_parts.append(f"{label}: {record[key]}")
    description = (
        "Public film-catalogue metadata permalink enumerated from the "
        "robots-declared IWM Film sitemap. MAR materializes metadata and the "
        "stable public record URL only; it does not download or redistribute "
        "audiovisual media and does not infer a licence to reproduce it."
    )
    if metadata_parts:
        description += " " + "; ".join(metadata_parts) + "."
    return {
        **_base_row(institution),
        "partner_site": IWM_FILM_HOME_URL,
        "platform": IWM_FILM_PLATFORM_LABEL,
        "video_link": record["page_url"],
        "video_title": record.get("title", ""),
        "video_subject": "IWM Film Archive record",
        "video_description": description,
        "video_published_at": record.get("date", ""),
    }


def collect_iwm_film_dataset(
    *,
    session=SESSION,
    robots_loader=_fetch_robots,
    fetch_allowed=_fetch_allowed,
):
    institutions = collect_iwm_film_institutions()
    institution = institutions[0]
    internal_pages = []
    fatal_errors = []

    robots_ok, robots_status, robots_text = robots_loader(session)
    if not robots_ok:
        internal_pages.append(
            _internal_page_row(
                institution,
                IWM_FILM_SITEMAP_INDEX_URL,
                "bloqueado_robots",
                warning="Enumeração abortada antes do sitemap index.",
                error=robots_status,
            )
        )
        summary = [
            {
                **_base_row(institution),
                "partner_site": IWM_FILM_HOME_URL,
                "partner_domain": normalize_domain(IWM_FILM_HOME_URL),
                "status": "sem_registros",
                "http_code": "",
                "integrity_status": "instavel",
                "final_url": IWM_FILM_SITEMAP_INDEX_URL,
                "video_links_found_total": 0,
                "embedded_video_signals_total": 0,
                "candidate_internal_pages": 1,
                "priority_review": True,
                "warning": (
                    "IWM Film confirmado, mas o sitemap index não pôde ser usado "
                    "sob a política fail-closed de robots."
                ),
                "error": robots_status,
            }
        ]
        return institutions, summary, [], internal_pages

    index_response = fetch_allowed(
        session,
        IWM_FILM_SITEMAP_INDEX_URL,
        robots_text,
    )
    if index_response.error or index_response.status_code != 200:
        fatal_errors.append(
            "sitemap_index: "
            f"{index_response.error or index_response.status_code}"
        )
        partitions = []
    else:
        partitions = parse_iwm_sitemap_index(index_response.text)

    internal_pages.append(
        _internal_page_row(
            institution,
            index_response.final_url or IWM_FILM_SITEMAP_INDEX_URL,
            "ok" if not index_response.error and index_response.status_code == 200 else "erro",
            index_response.status_code or "",
            count=len(partitions),
            warning=(
                "Índice público declarado por robots; "
                f"partições de registros anunciadas={len(partitions)}; "
                f"robots={robots_status}."
            ),
            error=(
                ""
                if not index_response.error and index_response.status_code == 200
                else str(index_response.error or index_response.status_code)
            ),
        )
    )
    if not partitions:
        fatal_errors.append("sitemap_index: no record sitemap partitions discovered")

    records_by_url = {}
    partition_sets = {}
    for partition_url in partitions:
        if not robots_allowed(robots_text, CRAWLER_TOKEN, partition_url):
            fatal_errors.append(f"{partition_url}: robots blocked")
            partition_sets[partition_url] = set()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    partition_url,
                    "bloqueado_robots",
                    warning="Partição obrigatória omitida.",
                    error="blocked_by_robots",
                )
            )
            continue

        response = fetch_allowed(session, partition_url, robots_text)
        if response.error or response.status_code != 200:
            fatal_errors.append(
                f"{partition_url}: {response.error or response.status_code}"
            )
            partition_sets[partition_url] = set()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    partition_url,
                    "erro",
                    response.status_code or "",
                    warning="Falha em partição record-sitemap obrigatória.",
                    error=str(response.error or response.status_code),
                )
            )
            continue

        parsed = parse_iwm_record_sitemap(response.text)
        urls = parsed["record_urls"]
        partition_sets[partition_url] = set(urls)
        partition_errors = []
        if not urls:
            partition_errors.append("empty record partition")
        if parsed["rejected_location_count"]:
            partition_errors.append(
                "rejected_locations="
                f"{parsed['rejected_location_count']}"
            )
        if parsed["duplicates"]:
            partition_errors.append(
                f"duplicate_urls={len(parsed['duplicates'])}"
            )
        for error in partition_errors:
            fatal_errors.append(f"{partition_url}: {error}")
        for page_url in urls:
            record_id = _RECORD_PATH_RE.match(urlparse(page_url).path).group(1)
            records_by_url.setdefault(
                page_url,
                {
                    "page_url": page_url,
                    "record_id": record_id,
                    "title": "",
                    "film_number": "",
                    "digitised": "",
                    "date": "",
                    "production_country": "",
                    "sound": "",
                    "physical_characteristics": "",
                    "technical_details": "",
                    "source_partition": partition_url,
                },
            )
        internal_pages.append(
            _internal_page_row(
                institution,
                response.final_url or partition_url,
                "erro" if partition_errors else "ok",
                response.status_code,
                count=len(urls),
                warning=(
                    "Partição sitemap de registros; "
                    f"locs declarados={parsed['url_count']}; "
                    f"permalinks únicos válidos={len(urls)}; "
                    f"robots={robots_status}."
                ),
                error=" | ".join(partition_errors),
            )
        )

    partition_items = list(partition_sets.items())
    cross_partition_duplicates = set()
    for index, (_, left) in enumerate(partition_items):
        for _, right in partition_items[index + 1 :]:
            cross_partition_duplicates.update(left.intersection(right))
    if cross_partition_duplicates:
        fatal_errors.append(
            f"cross_partition_duplicates={len(cross_partition_duplicates)}"
        )

    records = sorted(records_by_url.values(), key=lambda row: row["page_url"])
    detail_candidates = records[: min(IWM_FILM_MAX_DETAIL_PAGES, len(records))]
    semantic_confirmed = 0
    for record in detail_candidates:
        page_url = record["page_url"]
        if not robots_allowed(robots_text, CRAWLER_TOKEN, page_url):
            fatal_errors.append(f"{page_url}: sample blocked by robots")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "bloqueado_robots",
                    warning="Amostra semântica obrigatória não acessada.",
                    error="blocked_by_robots",
                )
            )
            continue

        response = fetch_allowed(session, page_url, robots_text)
        if response.error or response.status_code != 200:
            fatal_errors.append(
                f"{page_url}: sample fetch failed "
                f"({response.error or response.status_code})"
            )
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_url,
                    "erro",
                    response.status_code or "",
                    warning="Falha em amostra semântica obrigatória.",
                    error=str(response.error or response.status_code),
                )
            )
            continue

        detail = parse_iwm_detail_page(
            response.text,
            response.final_url or page_url,
        )
        if not detail["film_semantics_confirmed"]:
            fatal_errors.append(f"{page_url}: film_semantics_not_confirmed")
        else:
            semantic_confirmed += 1
        for key, value in detail.items():
            if key != "media_markers" and value not in ("", None, False):
                record[key] = value
        internal_pages.append(
            _internal_page_row(
                institution,
                response.final_url or page_url,
                "ok" if detail["film_semantics_confirmed"] else "erro",
                response.status_code,
                count=1,
                warning=(
                    "Ficha pública enriquecida e validada semanticamente; "
                    f"digitised={detail.get('digitised') or 'unknown'}."
                ),
                error=(
                    ""
                    if detail["film_semantics_confirmed"]
                    else "film_semantics_not_confirmed"
                ),
            )
        )

    expected_semantic_samples = min(IWM_FILM_MAX_DETAIL_PAGES, len(records))
    if semantic_confirmed != expected_semantic_samples:
        fatal_errors.append(
            "semantic_sample_incomplete="
            f"{semantic_confirmed}/{expected_semantic_samples}"
        )

    links = [_record_to_video_row(institution, record) for record in records]
    partition_complete = (
        bool(partitions)
        and len(partition_sets) == len(partitions)
        and all(partition_sets.get(url) for url in partitions)
    )
    integrity = (
        "integro"
        if links
        and partition_complete
        and semantic_confirmed == expected_semantic_samples
        and not fatal_errors
        else "instavel"
    )
    counts = ", ".join(
        f"{urlparse(url).path.rsplit('/', 1)[-1]}:"
        f"{len(partition_sets.get(url, set()))}"
        for url in partitions
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": IWM_FILM_HOME_URL,
            "partner_domain": normalize_domain(IWM_FILM_HOME_URL),
            "status": "ok" if links else "sem_registros",
            "http_code": 200 if links else "",
            "integrity_status": integrity,
            "final_url": IWM_FILM_SITEMAP_INDEX_URL,
            "video_links_found_total": len(links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": integrity != "integro",
            "warning": _clean_text(
                "Snapshot do IWM Film enumerado por todas as partições "
                "sitemap-records anunciadas pelo índice público nesta rodada. "
                f"A rodada materializou {len(links)} permalinks únicos em "
                f"{len(partitions)} partições ({counts}). "
                "As 25.000 horas declaradas pelo IWM são apenas contexto "
                "custodial e não denominador de completude web. "
                "A existência de ficha pública não implica digitalização, "
                "streaming ou licença de reprodução. Nenhuma mídia foi baixada. "
                f"Validação/enriquecimento determinístico limitado a "
                f"{IWM_FILM_MAX_DETAIL_PAGES} fichas; "
                f"semântica confirmada={semantic_confirmed}/"
                f"{expected_semantic_samples}."
            ),
            "error": " | ".join(fatal_errors[:12]),
        }
    ]
    return institutions, summary, links, internal_pages


__all__ = [
    "IWM_FILM_MAX_DETAIL_PAGES",
    "collect_iwm_film_dataset",
    "collect_iwm_film_institutions",
    "parse_iwm_detail_page",
    "parse_iwm_record_sitemap",
    "parse_iwm_sitemap_index",
]
