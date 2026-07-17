import html
import re

import requests
from bs4 import BeautifulSoup

from .config import (
    AUTREFOIS_HOME_URL,
    AUTREFOIS_TAGS_API_URL,
    AUTREFOIS_VIDEOS_API_URL,
    AUTREFOIS_VIDEOS_SITEMAP_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


AUTREFOIS_REPOSITORY_CODE = "CH-AUTREFOIS-GENEVE"
AUTREFOIS_ARCHIVE_TYPE = "Institutional audiovisual archive"
AUTREFOIS_COUNTRY = normalize_country("Switzerland")
AUTREFOIS_INSTITUTION_NAME = "Fondation Autrefois Genève"
AUTREFOIS_PLATFORM_LABEL = "Autrefois Genève"
AUTREFOIS_WP_PER_PAGE = 100

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _strip_html(value, *, limit=None):
    text = BeautifulSoup(html.unescape(str(value or "")), "html.parser").get_text(" ", strip=True)
    return _clean_text(text, limit=limit)


def _fetch(url, **kwargs):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True, **kwargs)


def _as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def collect_autrefois_institutions():
    return [
        {
            "institution": AUTREFOIS_INSTITUTION_NAME,
            "slug": slugify(AUTREFOIS_INSTITUTION_NAME),
            "country": AUTREFOIS_COUNTRY,
            "continent": country_to_continent(AUTREFOIS_COUNTRY),
            "repository_code": AUTREFOIS_REPOSITORY_CODE,
            "archive_type": AUTREFOIS_ARCHIVE_TYPE,
            "autrefois_detail_url": AUTREFOIS_HOME_URL,
            "external_url": AUTREFOIS_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _extract_video_source(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    source = soup.find("source", src=True)
    if source:
        return source.get("src", ""), source.get("type", "")
    video = soup.find("video", src=True)
    if video:
        return video.get("src", ""), video.get("type", "")
    iframe = soup.find("iframe", src=True)
    if iframe:
        return iframe.get("src", ""), ""
    return "", ""


def _load_tag_map():
    try:
        response = _fetch(AUTREFOIS_TAGS_API_URL, params={"per_page": AUTREFOIS_WP_PER_PAGE})
        response.raise_for_status()
        return {tag.get("id"): tag.get("name", "") for tag in response.json()}
    except Exception:
        return {}


def parse_autrefois_video_post(post, detail_html="", tag_map=None):
    tag_map = tag_map or {}
    title = _strip_html(post.get("title", {}).get("rendered", "")) or str(post.get("slug", ""))
    page_url = post.get("link", "")
    video_source, video_type = _extract_video_source(detail_html)
    description = _strip_html(
        post.get("content", {}).get("rendered") or post.get("excerpt", {}).get("rendered", ""),
        limit=900,
    )
    tags = ", ".join(
        sorted(
            dict.fromkeys(
                tag_map.get(tag_id, "")
                for tag_id in post.get("aiovg_tags", [])
                if tag_map.get(tag_id, "")
            )
        )
    )
    note = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do tipo WordPress `aiovg_videos` da Fondation Autrefois Genève.",
                f"tag: {tags}" if tags else "",
                f"fonte de vídeo: {video_type}" if video_type else "",
                description,
            ]
            if value
        ),
        limit=1000,
    )
    return {
        "record_id": str(post.get("id", "")),
        "source_kind": "wordpress_aiovg_videos",
        "video_link": video_source or page_url,
        "page_url": page_url,
        "platform": AUTREFOIS_PLATFORM_LABEL,
        "title": title,
        "subject": tags,
        "description": note,
        "date": str(post.get("date", ""))[:10],
        "embedded": bool(video_source),
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": AUTREFOIS_REPOSITORY_CODE,
        "archive_type": AUTREFOIS_ARCHIVE_TYPE,
        "autrefois_detail_url": AUTREFOIS_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": AUTREFOIS_VIDEOS_API_URL,
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
        "partner_site": AUTREFOIS_VIDEOS_API_URL,
        "platform": record.get("platform", AUTREFOIS_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_autrefois_dataset():
    institutions = collect_autrefois_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    errors = []
    total_expected = 0

    for url, warning in [
        (AUTREFOIS_HOME_URL, "Site institucional da Fondation Autrefois Genève."),
        (AUTREFOIS_VIDEOS_SITEMAP_URL, "Sitemap público do tipo `aiovg_videos`."),
        (AUTREFOIS_VIDEOS_API_URL, "Endpoint público WordPress `aiovg_videos`, usado como rota catalográfica online."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    tag_map = _load_tag_map()
    try:
        response = _fetch(
            AUTREFOIS_VIDEOS_API_URL,
            params={
                "per_page": AUTREFOIS_WP_PER_PAGE,
                "page": 1,
                "_fields": "id,date,slug,title,link,content,excerpt,aiovg_tags",
            },
        )
        response.raise_for_status()
        total_expected = _as_int(response.headers.get("X-WP-Total"))
        posts = response.json()
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(posts),
                0,
                "Página única do endpoint WordPress público `aiovg_videos`.",
            )
        )
        for post in posts:
            detail_html = ""
            try:
                detail_response = _fetch(post.get("link", ""))
                detail_response.raise_for_status()
                detail_html = detail_response.text
                video_source, _ = _extract_video_source(detail_html)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        detail_response.url,
                        "ok",
                        detail_response.status_code,
                        1 if video_source else 0,
                        1 if video_source else 0,
                        "Página pública `aiovg_videos`; player HTML verificado sem baixar mídia.",
                    )
                )
            except Exception as error:
                errors.append(f"{post.get('link', '')}: {error}")
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        post.get("link", ""),
                        "erro",
                        warning="Falha ao abrir página individual `aiovg_videos`.",
                        error=str(error),
                    )
                )
            records.append(parse_autrefois_video_post(post, detail_html, tag_map))
    except Exception as error:
        errors.append(f"aiovg_videos page 1: {error}")
        internal_pages.append(
            _internal_page_row(
                institution,
                f"{AUTREFOIS_VIDEOS_API_URL}?per_page={AUTREFOIS_WP_PER_PAGE}&page=1",
                "erro",
                warning="Falha no endpoint `aiovg_videos`; completude da rodada fica parcial.",
                error=str(error),
            )
        )

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_endpoint = bool(total_expected) and len(video_links) == total_expected and not errors
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary_warning = (
        "Corpus institucional incorporado pelo endpoint público WordPress `aiovg_videos` da Fondation Autrefois Genève. "
        f"A rodada materializou {len(video_links)} de {total_expected or len(video_links)} registros declarados pelo endpoint, "
        f"com {embedded_total} páginas contendo fonte de vídeo detectada. "
        "O recorte online não equivale ao acervo total da fundação."
    )
    if not complete_endpoint:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha ou divergência de paginação."

    summary = [
        {
            **_base_row(institution),
            "partner_site": AUTREFOIS_VIDEOS_API_URL,
            "partner_domain": normalize_domain(AUTREFOIS_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_endpoint else "acessivel" if video_links else "instavel",
            "final_url": AUTREFOIS_VIDEOS_API_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_endpoint else "media",
            "warning": summary_warning,
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "AUTREFOIS_WP_PER_PAGE",
    "collect_autrefois_dataset",
    "collect_autrefois_institutions",
    "parse_autrefois_video_post",
]
