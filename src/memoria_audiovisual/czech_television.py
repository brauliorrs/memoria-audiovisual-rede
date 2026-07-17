from __future__ import annotations

import json
import re
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    CZECH_TELEVISION_DOKUMENTY_CATALOG_URL,
    CZECH_TELEVISION_HISTORIE_CATALOG_URL,
    CZECH_TELEVISION_HOME_URL,
    CZECH_TELEVISION_IVYSILANI_URL,
    CZECH_TELEVISION_KULTURA_CATALOG_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CZECH_TELEVISION_REPOSITORY_CODE = "CZ-CT"
CZECH_TELEVISION_ARCHIVE_TYPE = "Public service broadcaster digital video archive"
CZECH_TELEVISION_COUNTRY = normalize_country("Czech Republic")
CZECH_TELEVISION_INSTITUTION_NAME = "Czech Television"
CZECH_TELEVISION_PLATFORM_LABEL = "Česká televize iVysílání"
CZECH_TELEVISION_MAX_SHOWS = 6
CZECH_TELEVISION_EPISODES_PER_SHOW = 2
CZECH_TELEVISION_REQUEST_PAUSE = 0.1

CZECH_TELEVISION_CATALOG_SEEDS = [
    ("Cultura", CZECH_TELEVISION_KULTURA_CATALOG_URL),
    ("Documentários", CZECH_TELEVISION_DOKUMENTY_CATALOG_URL),
    ("História", CZECH_TELEVISION_HISTORIE_CATALOG_URL),
]

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "cs,en;q=0.8,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    response.raise_for_status()
    return response


def _next_data(html):
    soup = BeautifulSoup(html or "", "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if not script:
        return {}
    try:
        return json.loads(script.string or script.get_text("", strip=True) or "{}")
    except json.JSONDecodeError:
        return {}


def _page_data(html):
    return _next_data(html).get("props", {}).get("pageProps", {}).get("data", {})


def _genre_titles(flat_genres):
    if not isinstance(flat_genres, list):
        return []
    titles = []
    for genre in flat_genres:
        title = _clean_text(genre.get("title") if isinstance(genre, dict) else genre)
        if title:
            titles.append(title)
    return list(dict.fromkeys(titles))


def parse_czech_television_catalog_page(html, category_label=""):
    category = _page_data(html).get("category", {})
    items = category.get("programmeFind", {}).get("items", [])
    records = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        slug = _clean_text(item.get("slug"))
        if not slug or not item.get("isPlayable"):
            continue
        records.append(
            {
                "show_id": _clean_text(item.get("id")),
                "show_slug": slug,
                "show_title": _clean_text(item.get("title")),
                "category_label": _clean_text(category_label),
                "genres": _genre_titles(item.get("flatGenres")),
                "show_url": urljoin(CZECH_TELEVISION_HOME_URL, f"/porady/{slug}/"),
                "is_playable": bool(item.get("isPlayable")),
            }
        )
    return records


def parse_czech_television_show_page(html, show_slug):
    normalized_html = (html or "").replace("\\u002F", "/")
    pattern = rf"/porady/{re.escape(show_slug)}/(\d+)/"
    episode_urls = []
    seen = set()

    soup = BeautifulSoup(html or "", "html.parser")
    for anchor in soup.select("a[href]"):
        href = anchor.get("href", "")
        match = re.search(pattern, href)
        if match:
            episode_url = urljoin(CZECH_TELEVISION_HOME_URL, f"/porady/{show_slug}/{match.group(1)}/")
            if episode_url not in seen:
                seen.add(episode_url)
                episode_urls.append(episode_url)

    for episode_id in re.findall(pattern, normalized_html):
        episode_url = urljoin(CZECH_TELEVISION_HOME_URL, f"/porady/{show_slug}/{episode_id}/")
        if episode_url not in seen:
            seen.add(episode_url)
            episode_urls.append(episode_url)

    return episode_urls


def parse_czech_television_episode_page(html, page_url, show_context=None):
    media = _page_data(html).get("mediaMeta", {})
    if not isinstance(media, dict) or not media.get("isPlayable"):
        return {}

    show_context = show_context or {}
    show = media.get("show") if isinstance(media.get("show"), dict) else {}
    genres = _genre_titles(show.get("flatGenres")) or show_context.get("genres", [])
    origin_countries = [
        _clean_text(country.get("title"))
        for country in media.get("countriesOfOrigin", [])
        if isinstance(country, dict) and _clean_text(country.get("title"))
    ]
    published_at = _clean_text(media.get("uploadDate"))
    if published_at:
        published_at = published_at[:10]
    else:
        published_at = _clean_text(media.get("year"))

    show_title = _clean_text(show.get("title") or show_context.get("show_title"))
    title = _clean_text(media.get("title") or show_title)
    duration = _clean_text(media.get("durationText"))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                _clean_text(media.get("description")),
                f"programa: {show_title}" if show_title else "",
                f"recorte: {show_context.get('category_label')}" if show_context.get("category_label") else "",
                f"gêneros: {', '.join(genres)}" if genres else "",
                f"duração: {duration}" if duration else "",
                f"ano: {media.get('year')}" if media.get("year") else "",
                f"país de origem: {', '.join(origin_countries)}" if origin_countries else "",
                "ficha pública do iVysílání com mediaMeta.isPlayable=True; mídia não baixada",
            ]
            if value
        ),
        limit=1400,
    )
    return {
        "record_id": _clean_text(media.get("id") or media.get("idec")),
        "show_title": show_title,
        "title": title,
        "subject": "; ".join(value for value in [show_title, *genres, show_context.get("category_label")] if value),
        "description": description,
        "date": published_at,
        "page_url": page_url,
        "duration": duration,
        "embedded": True,
    }


def collect_czech_television_institutions():
    return [
        {
            "institution": CZECH_TELEVISION_INSTITUTION_NAME,
            "slug": slugify("czech-television"),
            "country": CZECH_TELEVISION_COUNTRY,
            "continent": country_to_continent(CZECH_TELEVISION_COUNTRY),
            "repository_code": CZECH_TELEVISION_REPOSITORY_CODE,
            "archive_type": CZECH_TELEVISION_ARCHIVE_TYPE,
            "czech_tv_detail_url": CZECH_TELEVISION_IVYSILANI_URL,
            "external_url": CZECH_TELEVISION_HOME_URL,
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
        "repository_code": CZECH_TELEVISION_REPOSITORY_CODE,
        "archive_type": CZECH_TELEVISION_ARCHIVE_TYPE,
        "czech_tv_detail_url": CZECH_TELEVISION_IVYSILANI_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CZECH_TELEVISION_IVYSILANI_URL,
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
        "partner_site": record.get("page_url") or CZECH_TELEVISION_IVYSILANI_URL,
        "platform": CZECH_TELEVISION_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_czech_television_dataset():
    institutions = collect_czech_television_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_url = {}
    errors = []

    for url, warning in [
        (CZECH_TELEVISION_HOME_URL, "Site institucional da Czech Television."),
        (CZECH_TELEVISION_IVYSILANI_URL, "Plataforma pública iVysílání de vídeos sob demanda."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    selected_shows = []
    seen_shows = set()
    for category_label, catalog_url in CZECH_TELEVISION_CATALOG_SEEDS:
        try:
            response = _fetch(catalog_url)
            shows = parse_czech_television_catalog_page(response.text, category_label)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(shows),
                    0,
                    f"Catálogo público iVysílání: {category_label}.",
                )
            )
        except Exception as error:
            errors.append(f"{catalog_url}: {error}")
            internal_pages.append(_internal_page_row(institution, catalog_url, "erro", warning=f"Falha no catálogo {category_label}.", error=str(error)))
            continue

        for show in shows:
            if show["show_slug"] in seen_shows:
                continue
            seen_shows.add(show["show_slug"])
            selected_shows.append(show)
            if len(selected_shows) >= CZECH_TELEVISION_MAX_SHOWS:
                break
        if len(selected_shows) >= CZECH_TELEVISION_MAX_SHOWS:
            break

    for show in selected_shows:
        try:
            show_response = _fetch(show["show_url"])
            episode_urls = parse_czech_television_show_page(show_response.text, show["show_slug"])
            internal_pages.append(
                _internal_page_row(
                    institution,
                    show_response.url,
                    "ok",
                    show_response.status_code,
                    len(episode_urls),
                    0,
                    f"Página de programa iVysílání: {show['show_title']}.",
                )
            )
        except Exception as error:
            errors.append(f"{show['show_url']}: {error}")
            internal_pages.append(_internal_page_row(institution, show["show_url"], "erro", warning="Falha ao abrir programa iVysílání.", error=str(error)))
            continue

        for episode_url in episode_urls[:CZECH_TELEVISION_EPISODES_PER_SHOW]:
            if episode_url in records_by_url:
                continue
            try:
                episode_response = _fetch(episode_url)
                record = parse_czech_television_episode_page(episode_response.text, episode_response.url, show)
                if record:
                    records_by_url[episode_response.url] = record
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        episode_response.url,
                        "ok",
                        episode_response.status_code,
                        1 if record else 0,
                        1 if record.get("embedded") else 0,
                        "Ficha de episódio iVysílání verificada por __NEXT_DATA__/mediaMeta.",
                    )
                )
            except Exception as error:
                errors.append(f"{episode_url}: {error}")
                internal_pages.append(_internal_page_row(institution, episode_url, "erro", warning="Falha ao abrir episódio iVysílání.", error=str(error)))
            time.sleep(CZECH_TELEVISION_REQUEST_PAUSE)

    records = list(records_by_url.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("page_url")]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CZECH_TELEVISION_IVYSILANI_URL,
            "partner_domain": normalize_domain(CZECH_TELEVISION_IVYSILANI_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": CZECH_TELEVISION_KULTURA_CATALOG_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(1 for record in records if record.get("embedded")),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": (
                "Corpus institucional incorporado por rota pública do iVysílání. A fonte identificadora "
                "na fila é o EUscreen, mas a unidade analítica aqui é a Czech Television como arquivo "
                "televisivo público individual. Recorte MVP: primeiras categorias públicas cultura, "
                "documentários e história, até seis programas reproduzíveis e dois episódios por programa; "
                "não é catálogo completo e não baixa mídia."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CZECH_TELEVISION_ARCHIVE_TYPE",
    "CZECH_TELEVISION_CATALOG_SEEDS",
    "CZECH_TELEVISION_INSTITUTION_NAME",
    "CZECH_TELEVISION_PLATFORM_LABEL",
    "CZECH_TELEVISION_REPOSITORY_CODE",
    "collect_czech_television_dataset",
    "collect_czech_television_institutions",
    "parse_czech_television_catalog_page",
    "parse_czech_television_episode_page",
    "parse_czech_television_show_page",
]
