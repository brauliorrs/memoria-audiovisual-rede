from __future__ import annotations

import html
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    CSC_CINETECA_CONSULTATION_URL,
    CSC_CINETECA_FILM_ARCHIVE_URL,
    CSC_CINETECA_HOME_URL,
    CSC_CINETECA_VIDEO_CATALOG_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CSC_CINETECA_INSTITUTION_NAME = (
    "Fondazione Centro Sperimentale di Cinematografia - Cineteca Nazionale"
)
CSC_CINETECA_REPOSITORY_CODE = "IT-CSC-CINETECA"
CSC_CINETECA_ARCHIVE_TYPE = "National film archive with public video catalog"
CSC_CINETECA_COUNTRY = normalize_country("Italy")
CSC_CINETECA_PLATFORM_LABEL = "CSC / Cineteca Nazionale"
CSC_CINETECA_MIN_CATALOG_PAGE_TOTAL = 82
CSC_CINETECA_MIN_VIDEO_TOTAL = 80
CSC_CINETECA_DETAIL_WORKERS = 6
CSC_CINETECA_REQUEST_PAUSE = 0.05

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7",
        "Referer": CSC_CINETECA_VIDEO_CATALOG_URL,
    }
)


def _clean_text(value, *, limit=None):
    raw = html.unescape(str(value or ""))
    text = BeautifulSoup(raw, "html.parser").get_text(" ", strip=True) if "<" in raw else raw
    text = re.sub(r"\s+", " ", text).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)


def _meta_content(soup, *selectors):
    for selector in selectors:
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            return _clean_text(tag["content"])
    return ""


def _strip_site_suffix(title):
    return re.sub(r"\s+-\s+Centro Sperimentale di Cinematografia\s*$", "", _clean_text(title))


def extract_csc_cineteca_catalog_links(html_text, base_url=CSC_CINETECA_VIDEO_CATALOG_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base_url, anchor["href"]).split("#")[0].split("?")[0]
        if "/en/" in href or "/film/" not in href:
            continue
        if href.rstrip("/") == "https://www.fondazionecsc.it/film":
            continue
        links.append(href)
    return list(dict.fromkeys(links))


def _normalize_youtube_url(source):
    parsed = urlparse(source)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    video_id = ""
    if "youtu.be" in host:
        video_id = path.split("/")[0]
    elif "youtube" in host:
        if path.startswith("embed/"):
            video_id = path.split("/", 1)[1].split("/")[0]
        else:
            video_id = parse_qs(parsed.query).get("v", [""])[0]
    return f"https://www.youtube.com/watch?v={video_id}" if video_id else source


def _normalize_vimeo_url(source):
    match = re.search(r"(?:player\.)?vimeo\.com/(?:video/)?(\d+)", source)
    return f"https://vimeo.com/{match.group(1)}" if match else source


def normalize_csc_cineteca_media_url(source):
    source = _clean_text(source)
    if not source:
        return ""
    if "youtube" in source or "youtu.be" in source:
        return _normalize_youtube_url(source)
    if "vimeo.com" in source:
        return _normalize_vimeo_url(source)
    return source


def _media_platform(media_url):
    normalized = media_url.lower()
    if "youtube.com" in normalized or "youtu.be" in normalized:
        return "YouTube"
    if "vimeo.com" in normalized:
        return "Vimeo"
    return CSC_CINETECA_PLATFORM_LABEL


def _extract_embed_sources(soup, page_url):
    sources = []
    for tag in soup.find_all(["iframe", "embed", "video", "source"]):
        source = tag.get("src") or tag.get("data-src")
        if source:
            sources.append(urljoin(page_url, source))
    raw_html = str(soup)
    sources.extend(
        match.group(0)
        for match in re.finditer(
            r"https?://(?:www\.)?(?:youtube(?:-nocookie)?\.com/embed|youtu\.be)/[A-Za-z0-9_-]+[^\"'\s<>]*",
            raw_html,
            flags=re.I,
        )
    )
    sources.extend(
        match.group(0)
        for match in re.finditer(
            r"https?://player\.vimeo\.com/video/\d+[^\"'\s<>]*",
            raw_html,
            flags=re.I,
        )
    )
    normalized = [normalize_csc_cineteca_media_url(source) for source in sources]
    return [source for source in dict.fromkeys(normalized) if source]


def _jsonld_objects(soup):
    objects = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.string or script.get_text() or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            objects.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            graph = payload.get("@graph")
            if isinstance(graph, list):
                objects.extend(item for item in graph if isinstance(item, dict))
            objects.append(payload)
    return objects


def _jsonld_first(soup, *keys):
    for item in _jsonld_objects(soup):
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return _clean_text(value)
    return ""


def _extract_page_description(soup):
    soup_copy = BeautifulSoup(str(soup), "html.parser")
    main = soup_copy.find("main") or soup_copy.find("article") or soup_copy
    for tag in main.find_all(["script", "style", "nav", "header", "footer", "iframe"]):
        tag.decompose()
    return _clean_text(main.get_text(" ", strip=True), limit=900)


def parse_csc_cineteca_video_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title = (
        _meta_content(soup, "meta[property='og:title']", "meta[name='twitter:title']")
        or _jsonld_first(soup, "headline", "name")
        or _clean_text(soup.title.string if soup.title else "")
    )
    title = _strip_site_suffix(title) or page_url
    media_sources = _extract_embed_sources(soup, page_url)
    media_url = media_sources[0] if media_sources else ""
    description = (
        _meta_content(soup, "meta[property='og:description']", "meta[name='description']")
        or _jsonld_first(soup, "description")
        or _extract_page_description(soup)
    )
    published_at = (
        _jsonld_first(soup, "datePublished", "uploadDate", "dateCreated")
        or _meta_content(soup, "meta[property='article:published_time']")
    )
    return {
        "record_id": page_url.rstrip("/").rsplit("/", 1)[-1],
        "video_link": media_url or page_url,
        "page_url": page_url,
        "platform": _media_platform(media_url),
        "title": title,
        "subject": "Catalogo video della Cineteca Nazionale; cinema; patrimônio fílmico",
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública do Catalogo video da Cineteca Nazionale/CSC.",
                    description,
                    f"player público: {media_url}" if media_url else "sem player público detectado na rodada",
                ]
                if value
            ),
            limit=1200,
        ),
        "date": published_at[:10] if published_at else "",
        "media_sources": media_sources,
        "embedded": bool(media_url),
    }


def collect_csc_cineteca_institutions():
    return [
        {
            "institution": CSC_CINETECA_INSTITUTION_NAME,
            "slug": slugify(CSC_CINETECA_INSTITUTION_NAME),
            "country": CSC_CINETECA_COUNTRY,
            "continent": country_to_continent(CSC_CINETECA_COUNTRY),
            "repository_code": CSC_CINETECA_REPOSITORY_CODE,
            "archive_type": CSC_CINETECA_ARCHIVE_TYPE,
            "csc_cineteca_detail_url": CSC_CINETECA_HOME_URL,
            "external_url": CSC_CINETECA_VIDEO_CATALOG_URL,
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
        "repository_code": CSC_CINETECA_REPOSITORY_CODE,
        "archive_type": CSC_CINETECA_ARCHIVE_TYPE,
        "csc_cineteca_detail_url": CSC_CINETECA_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CSC_CINETECA_VIDEO_CATALOG_URL,
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
        "partner_site": CSC_CINETECA_VIDEO_CATALOG_URL,
        "platform": record.get("platform", CSC_CINETECA_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_video_page(url):
    try:
        response = _fetch(url)
        response.raise_for_status()
        return url, response.url, response.status_code, response.text, ""
    except Exception as error:
        return url, url, "", "", str(error)


def collect_csc_cineteca_dataset():
    institutions = collect_csc_cineteca_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    errors = []
    catalog_links = []

    for url, warning in [
        (CSC_CINETECA_HOME_URL, "Página institucional da Cineteca Nazionale."),
        (
            CSC_CINETECA_FILM_ARCHIVE_URL,
            "Página oficial do Archivio Film; confirma acervo amplo, distinto do corpus público online.",
        ),
        (
            CSC_CINETECA_CONSULTATION_URL,
            "Página de consulta; informa acesso por estudo/agendamento e impede confundir acervo total com corpus online.",
        ),
        (
            CSC_CINETECA_VIDEO_CATALOG_URL,
            "Catalogo video oficial usado como unidade metodológica pública e enumerável.",
        ),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            if url == CSC_CINETECA_VIDEO_CATALOG_URL:
                catalog_links = extract_csc_cineteca_catalog_links(response.text, response.url)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(catalog_links) if url == CSC_CINETECA_VIDEO_CATALOG_URL else 0,
                    0,
                    warning,
                )
            )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    with ThreadPoolExecutor(max_workers=CSC_CINETECA_DETAIL_WORKERS) as executor:
        futures = {executor.submit(_fetch_video_page, url): url for url in catalog_links}
        for future in as_completed(futures):
            requested_url, final_url, status_code, detail_html, error = future.result()
            if error:
                errors.append(f"{requested_url}: {error}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        requested_url,
                        "erro",
                        warning="Falha ao abrir ficha pública do Catalogo video.",
                        error=error,
                    )
                )
                continue
            parsed = parse_csc_cineteca_video_page(detail_html, final_url)
            records.append(parsed)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    final_url,
                    "ok",
                    status_code,
                    1 if parsed.get("embedded") else 0,
                    1 if parsed.get("embedded") else 0,
                    "Ficha pública do Catalogo video verificada sem baixar mídia.",
                )
            )
            time.sleep(CSC_CINETECA_REQUEST_PAUSE)

    deduped_records = []
    seen_links = set()
    for record in sorted(records, key=lambda item: item.get("page_url", "")):
        video_link = record.get("video_link", "")
        if not video_link or video_link in seen_links:
            continue
        seen_links.add(video_link)
        deduped_records.append(record)

    video_links = [_record_to_video_row(institution, record) for record in deduped_records if record.get("embedded")]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    complete = (
        len(catalog_links) >= CSC_CINETECA_MIN_CATALOG_PAGE_TOTAL
        and embedded_total == len(catalog_links)
        and len(video_links) >= CSC_CINETECA_MIN_VIDEO_TOTAL
    )
    platform_counts = {}
    for record in records:
        if record.get("embedded"):
            platform_counts[record["platform"]] = platform_counts.get(record["platform"], 0) + 1
    platform_note = ", ".join(f"{platform}: {count}" for platform, count in sorted(platform_counts.items()))

    summary = [
        {
            **_base_row(institution),
            "partner_site": CSC_CINETECA_VIDEO_CATALOG_URL,
            "partner_domain": normalize_domain(CSC_CINETECA_HOME_URL),
            "status": "ok" if video_links else "sem_video_publico",
            "http_code": "200" if catalog_links else "",
            "integrity_status": "integro" if complete else "instavel",
            "final_url": CSC_CINETECA_VIDEO_CATALOG_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": len(video_links) < CSC_CINETECA_MIN_VIDEO_TOTAL or not complete,
            "warning": (
                f"O Catalogo video oficial listou {len(catalog_links)} fichas públicas; a rodada incorporou "
                f"{embedded_total} fichas com player público ({platform_note or 'plataforma não identificada'}) e "
                f"{len(video_links)} URLs de vídeo únicas após deduplicação. "
                "A página institucional informa acervo fílmico amplo e consulta por estudo/agendamento; portanto "
                "o corpus incorporado representa somente a superfície pública online enumerável, não o acervo "
                "físico, interno, licenciado ou não publicado da Cineteca Nazionale."
            ),
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CSC_CINETECA_MIN_CATALOG_PAGE_TOTAL",
    "CSC_CINETECA_MIN_VIDEO_TOTAL",
    "collect_csc_cineteca_dataset",
    "collect_csc_cineteca_institutions",
    "extract_csc_cineteca_catalog_links",
    "normalize_csc_cineteca_media_url",
    "parse_csc_cineteca_video_page",
]
