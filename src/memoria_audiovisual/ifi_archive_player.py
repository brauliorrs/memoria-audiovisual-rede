from __future__ import annotations

import re
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    IFI_ARCHIVE_PLAYER_HOME_URL,
    IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country
from .ifi_archive_player_probe import CRAWLER_TOKEN, robots_allowed


IFI_ARCHIVE_PLAYER_INSTITUTION_NAME = "IFI Irish Film Archive"
IFI_ARCHIVE_PLAYER_REPOSITORY_CODE = "IE-IFI-IFA"
IFI_ARCHIVE_PLAYER_ARCHIVE_TYPE = "National film archive"
IFI_ARCHIVE_PLAYER_COUNTRY = normalize_country("Ireland")
IFI_ARCHIVE_PLAYER_PLATFORM_LABEL = "IFI Archive Player"
IFI_ARCHIVE_PLAYER_ROBOTS_URL = "https://ifiarchiveplayer.ie/robots.txt"
IFI_ARCHIVE_PLAYER_MAX_DETAIL_PAGES = 24
_POST_SITEMAP_RE = re.compile(
    r"^https://ifiarchiveplayer\.ie/post-sitemap(?:\d+)?\.xml$",
    re.I,
)
_XML_LOC_RE = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)
_EXCLUDED_ROOTS = {
    "",
    "about",
    "app",
    "browse",
    "collections",
    "contact",
    "donate",
    "legal",
    "privacy-policy",
    "terms-conditions",
    "cookie-information",
    "ifi-platforms",
    "virtual-exhibitions",
    "wp-admin",
    "wp-json",
    "feed",
}

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "User-Agent": f"{CRAWLER_TOKEN}/1.0 (+research; public-metadata-collector)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IE,en;q=0.9",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = None
    for attempt in range(4):
        response = SESSION.get(
            url,
            timeout=(8, REQUEST_TIMEOUT),
            allow_redirects=True,
        )
        if response.status_code not in {429, 503}:
            return response
        time.sleep(float(attempt + 1))
    return response


def _valid_robots_payload(response):
    if response.status_code in {404, 410}:
        return True, "robots_absent", ""
    if response.status_code != 200:
        return False, f"robots_http_{response.status_code}", ""
    text = response.text or ""
    stripped = text.strip()
    if not stripped or "<html" in stripped.lower():
        return False, "robots_invalid_payload", ""
    return True, "robots_evaluated_rfc9309", text


def _robots_allowed(url):
    try:
        response = SESSION.get(
            IFI_ARCHIVE_PLAYER_ROBOTS_URL,
            timeout=(8, REQUEST_TIMEOUT),
            allow_redirects=True,
        )
    except requests.RequestException:
        return False, "robots_unreachable"
    valid, status, text = _valid_robots_payload(response)
    if not valid:
        return False, status
    if status == "robots_absent":
        return True, status
    return robots_allowed(text, CRAWLER_TOKEN, url), status


def _likely_film_permalink(url):
    parsed = urlparse(str(url or ""))
    if parsed.netloc.lower() != "ifiarchiveplayer.ie":
        return False
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 1:
        return False
    slug = parts[0].lower()
    if slug in _EXCLUDED_ROOTS or slug.endswith(".xml"):
        return False
    if slug.startswith(("category", "tag", "author", "wp-")):
        return False
    return True


def parse_ifi_sitemap_index(xml_text):
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    return sorted({url for url in urls if _POST_SITEMAP_RE.match(url)})


def parse_ifi_post_sitemap(xml_text):
    urls = [_clean_text(value) for value in _XML_LOC_RE.findall(xml_text or "")]
    return sorted({url for url in urls if _likely_film_permalink(url)})


def _label_value(soup, label):
    label_re = re.compile(rf"^{re.escape(label)}\s*:?", re.I)
    for node in soup.find_all(["dt", "th", "strong", "b", "p", "div", "span", "li"]):
        text = _clean_text(node.get_text(" ", strip=True), limit=1200)
        if not label_re.search(text):
            continue
        remainder = label_re.sub("", text, count=1).strip(" :-")
        if remainder:
            return _clean_text(remainder, limit=500)
        sibling = node.find_next_sibling()
        if sibling is not None:
            value = _clean_text(sibling.get_text(" ", strip=True), limit=500)
            if value:
                return value
    full_text = _clean_text(soup.get_text(" ", strip=True), limit=20000)
    match = re.search(
        rf"{re.escape(label)}\s*:\s*(.+?)(?=\s+(?:Category|Directed by|Produced by|Year|Duration|Language)\s*:|$)",
        full_text,
        re.I,
    )
    return _clean_text(match.group(1), limit=500) if match else ""


def parse_ifi_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    heading = soup.find("h1") or soup.find("h2")
    title = _clean_text(
        heading.get_text(" ", strip=True) if heading else "",
        limit=500,
    )
    return {
        "page_url": page_url,
        "title": title,
        "category": _label_value(soup, "Category"),
        "director": _label_value(soup, "Directed by"),
        "producer": _label_value(soup, "Produced by"),
        "date": _label_value(soup, "Year"),
        "duration": _label_value(soup, "Duration"),
        "language": _label_value(soup, "Language"),
    }


def collect_ifi_archive_player_institutions():
    return [
        {
            "institution": IFI_ARCHIVE_PLAYER_INSTITUTION_NAME,
            "slug": slugify(IFI_ARCHIVE_PLAYER_INSTITUTION_NAME),
            "country": IFI_ARCHIVE_PLAYER_COUNTRY,
            "continent": country_to_continent(IFI_ARCHIVE_PLAYER_COUNTRY),
            "repository_code": IFI_ARCHIVE_PLAYER_REPOSITORY_CODE,
            "archive_type": IFI_ARCHIVE_PLAYER_ARCHIVE_TYPE,
            "ifi_archive_player_detail_url": IFI_ARCHIVE_PLAYER_HOME_URL,
            "external_url": IFI_ARCHIVE_PLAYER_HOME_URL,
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
        "repository_code": IFI_ARCHIVE_PLAYER_REPOSITORY_CODE,
        "archive_type": IFI_ARCHIVE_PLAYER_ARCHIVE_TYPE,
        "ifi_archive_player_detail_url": IFI_ARCHIVE_PLAYER_HOME_URL,
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
        "partner_site": IFI_ARCHIVE_PLAYER_HOME_URL,
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
        ("category", "Category"),
        ("director", "Directed by"),
        ("producer", "Produced by"),
        ("duration", "Duration"),
        ("language", "Language"),
    ):
        if record.get(key):
            metadata_parts.append(f"{label}: {record[key]}")
    description = (
        "Public film-page metadata exposed by the IFI Archive Player. "
        "The permalink represents a public viewing/metadata surface; MAR does not "
        "download or redistribute the audiovisual media and does not infer a licence "
        "to reproduce it."
    )
    if metadata_parts:
        description += " " + "; ".join(metadata_parts) + "."
    return {
        **_base_row(institution),
        "partner_site": IFI_ARCHIVE_PLAYER_HOME_URL,
        "platform": IFI_ARCHIVE_PLAYER_PLATFORM_LABEL,
        "video_link": record["page_url"],
        "video_title": record.get("title", ""),
        "video_subject": record.get("category") or "IFI Archive Player film record",
        "video_description": description,
        "video_published_at": record.get("date", ""),
    }


def collect_ifi_archive_player_dataset(
    fetch=_fetch,
    robots_checker=_robots_allowed,
):
    institutions = collect_ifi_archive_player_institutions()
    institution = institutions[0]
    internal_pages = []
    fatal_errors = []
    detail_warnings = []

    allowed, robots_status = robots_checker(IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL)
    if not allowed:
        internal_pages.append(
            _internal_page_row(
                institution,
                IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL,
                "bloqueado_robots",
                warning="Enumeração interrompida antes do sitemap index.",
                error=robots_status,
            )
        )
        summary = [
            {
                **_base_row(institution),
                "partner_site": IFI_ARCHIVE_PLAYER_HOME_URL,
                "partner_domain": normalize_domain(IFI_ARCHIVE_PLAYER_HOME_URL),
                "status": "sem_registros",
                "http_code": "",
                "integrity_status": "instavel",
                "final_url": IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL,
                "video_links_found_total": 0,
                "embedded_video_signals_total": 0,
                "candidate_internal_pages": 1,
                "priority_review": True,
                "warning": (
                    "IFI Archive Player confirmado, mas a enumeração foi bloqueada "
                    "pela política fail-closed de robots."
                ),
                "error": robots_status,
            }
        ]
        return institutions, summary, [], internal_pages

    try:
        index_response = fetch(IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL)
        index_response.raise_for_status()
        partitions = parse_ifi_sitemap_index(index_response.text)
        internal_pages.append(
            _internal_page_row(
                institution,
                index_response.url,
                "ok",
                index_response.status_code,
                count=len(partitions),
                warning=(
                    "Índice público de sitemaps; "
                    f"post-sitemaps anunciados={len(partitions)}; robots={robots_status}."
                ),
            )
        )
    except Exception as error:
        partitions = []
        fatal_errors.append(f"sitemap_index: {error}")

    if not partitions:
        fatal_errors.append("sitemap_index: no post-sitemap partitions discovered")

    records_by_url = {}
    partition_sets = {}
    for partition_url in partitions:
        allowed_partition, partition_robots = robots_checker(partition_url)
        if not allowed_partition:
            fatal_errors.append(
                f"{partition_url}: robots blocked ({partition_robots})"
            )
            partition_sets[partition_url] = set()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    partition_url,
                    "bloqueado_robots",
                    warning="Partição obrigatória omitida.",
                    error=partition_robots,
                )
            )
            continue
        try:
            response = fetch(partition_url)
            response.raise_for_status()
            urls = parse_ifi_post_sitemap(response.text)
            partition_sets[partition_url] = set(urls)
            if not urls:
                fatal_errors.append(f"{partition_url}: empty partition")
            for page_url in urls:
                records_by_url.setdefault(
                    page_url,
                    {
                        "page_url": page_url,
                        "title": page_url.rstrip("/").rsplit("/", 1)[-1].replace("-", " "),
                        "date": "",
                        "category": "",
                        "director": "",
                        "producer": "",
                        "duration": "",
                        "language": "",
                        "source_partition": partition_url,
                    },
                )
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    count=len(urls),
                    warning=(
                        f"Partição post-sitemap; permalinks únicos={len(urls)}; "
                        f"robots={partition_robots}."
                    ),
                )
            )
        except Exception as error:
            partition_sets[partition_url] = set()
            fatal_errors.append(f"{partition_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    partition_url,
                    "erro",
                    warning="Falha em partição post-sitemap obrigatória.",
                    error=str(error),
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
    for record in records[:IFI_ARCHIVE_PLAYER_MAX_DETAIL_PAGES]:
        allowed_detail, detail_robots = robots_checker(record["page_url"])
        if not allowed_detail:
            detail_warnings.append(
                f"{record['page_url']}: robots blocked ({detail_robots})"
            )
            continue
        try:
            response = fetch(record["page_url"])
            response.raise_for_status()
            detail = parse_ifi_detail_page(response.text, response.url)
            for key, value in detail.items():
                if value:
                    record[key] = value
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    count=1,
                    warning=(
                        "Ficha pública enriquecida deterministicamente; "
                        f"robots={detail_robots}."
                    ),
                )
            )
        except Exception as error:
            detail_warnings.append(f"{record['page_url']}: {error}")

    links = [_record_to_video_row(institution, record) for record in records]
    partition_complete = (
        bool(partitions)
        and len(partition_sets) == len(partitions)
        and all(partition_sets.get(url) for url in partitions)
    )
    integrity = (
        "integro"
        if links and partition_complete and not fatal_errors
        else "instavel"
    )
    counts = ", ".join(
        f"{urlparse(url).path.lstrip('/') or url}:{len(partition_sets.get(url, set()))}"
        for url in partitions
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": IFI_ARCHIVE_PLAYER_HOME_URL,
            "partner_domain": normalize_domain(IFI_ARCHIVE_PLAYER_HOME_URL),
            "status": "ok" if links else "sem_registros",
            "http_code": 200 if links else "",
            "integrity_status": integrity,
            "final_url": IFI_ARCHIVE_PLAYER_SITEMAP_INDEX_URL,
            "video_links_found_total": len(links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": integrity != "integro",
            "warning": _clean_text(
                "Snapshot do IFI Archive Player enumerado por todas as partições "
                "post-sitemap anunciadas pelo índice público na rodada. "
                f"A rodada materializou {len(links)} permalinks únicos em "
                f"{len(partitions)} partições ({counts}). "
                "A declaração institucional de mais de 1.000 filmes é contexto da "
                "plataforma e não denominador de completude. O acervo físico do IFI é "
                "mais amplo e também não é denominador. Permalinks públicos não implicam "
                "licença para download, cópia ou redistribuição da mídia. "
                f"Enriquecimento determinístico limitado a "
                f"{IFI_ARCHIVE_PLAYER_MAX_DETAIL_PAGES} fichas. "
                f"Avisos não fatais de detalhe={len(detail_warnings)}."
            ),
            "error": " | ".join(fatal_errors[:12]),
        }
    ]
    return institutions, summary, links, internal_pages


__all__ = [
    "IFI_ARCHIVE_PLAYER_MAX_DETAIL_PAGES",
    "collect_ifi_archive_player_dataset",
    "collect_ifi_archive_player_institutions",
    "parse_ifi_detail_page",
    "parse_ifi_post_sitemap",
    "parse_ifi_sitemap_index",
]
