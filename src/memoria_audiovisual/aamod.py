import html
import re
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    AAMOD_ARCHIVI_ONLINE_URL,
    AAMOD_FAQ_URL,
    AAMOD_FILMOTECA_OPAC_URL,
    AAMOD_HOME_URL,
    AAMOD_PATRIMONIO_URL,
    AAMOD_WP_FILMS_URL,
    REQUEST_TIMEOUT,
)
from .crawler import classify_platform, normalize_domain, slugify
from .geography import country_to_continent, normalize_country


AAMOD_REPOSITORY_CODE = "IT-AAMOD"
AAMOD_ARCHIVE_TYPE = "Institutional audiovisual archive"
AAMOD_COUNTRY = normalize_country("Italy")
AAMOD_INSTITUTION_NAME = "Archivio Audiovisivo del movimento operaio e democratico"
AAMOD_PLATFORM_LABEL = "AAMOD"
AAMOD_CATALOG_URLS = [AAMOD_ARCHIVI_ONLINE_URL, AAMOD_FILMOTECA_OPAC_URL]
AAMOD_SEED_URLS = [AAMOD_HOME_URL, AAMOD_PATRIMONIO_URL, AAMOD_FAQ_URL]

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
        ),
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8,pt-BR;q=0.7",
    }
)


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _strip_html(value, *, limit=None):
    text = BeautifulSoup(html.unescape(str(value or "")), "html.parser").get_text(" ", strip=True)
    return _clean_text(text, limit=limit)


def _youtube_watch_url(embed_url):
    parsed = urlparse(embed_url)
    video_id = parsed.path.rstrip("/").split("/")[-1]
    query = parse_qs(parsed.query)
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    if query.get("start"):
        watch_url = f"{watch_url}&t={query['start'][0]}s"
    return watch_url


def _youtube_oembed(video_url):
    try:
        response = SESSION.get(
            "https://www.youtube.com/oembed",
            params={"url": video_url, "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def collect_aamod_institutions():
    return [
        {
            "institution": AAMOD_INSTITUTION_NAME,
            "slug": slugify(AAMOD_INSTITUTION_NAME),
            "country": AAMOD_COUNTRY,
            "continent": country_to_continent(AAMOD_COUNTRY),
            "repository_code": AAMOD_REPOSITORY_CODE,
            "archive_type": AAMOD_ARCHIVE_TYPE,
            "aamod_detail_url": AAMOD_HOME_URL,
            "external_url": AAMOD_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_aamod_home_page(html_text, page_url=AAMOD_HOME_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for iframe in soup.find_all("iframe", src=True):
        src = urljoin(page_url, iframe["src"])
        if classify_platform(src) != "YouTube":
            continue
        video_url = _youtube_watch_url(src)
        base_url = video_url.split("&t=", 1)[0]
        if base_url in seen:
            continue
        seen.add(base_url)
        oembed = _youtube_oembed(base_url)
        records.append(
            {
                "record_id": base_url.rsplit("=", 1)[-1],
                "source_kind": "youtube_embed",
                "video_link": video_url,
                "platform": "YouTube",
                "title": _clean_text(oembed.get("title")) or base_url,
                "subject": "Canal YouTube oficial do AAMOD",
                "description": (
                    "Vídeo incorporado na página oficial do AAMOD; "
                    f"autor no oEmbed: {_clean_text(oembed.get('author_name')) or 'não informado'}."
                ),
                "date": "",
                "embedded": True,
            }
        )
    return records


def _metadata_from_text(content):
    metadata = {}
    for key in ("genere", "regia di", "anno", "durata"):
        match = re.search(rf"{re.escape(key)}:\s*([^:]+?)(?=\s+(?:genere|regia di|anno|durata):|$)", content, re.I)
        if match:
            metadata[key] = _clean_text(match.group(1))
    return metadata


def _film_record_from_text(record_id, title, link, content, fallback_date=""):
    if not title:
        title_match = re.match(r"(.+?)\s+genere:", content, re.I)
        title = _clean_text(title_match.group(1)) if title_match else ""
    metadata = _metadata_from_text(content)
    description = re.sub(
        rf"^{re.escape(title)}\s*",
        "",
        content,
        flags=re.I,
    )
    description = re.sub(
        r"^genere:\s*.*?durata:\s*[\d:\s]+",
        "",
        description,
        flags=re.I,
    )
    return {
        "record_id": str(record_id),
        "source_kind": "film_record",
        "video_link": link,
        "platform": AAMOD_PLATFORM_LABEL,
        "title": title,
        "subject": metadata.get("genere", ""),
        "description": _clean_text(
            " | ".join(
                value
                for value in [
                    "Registro descritivo de filme no site oficial do AAMOD, sem player detectado na ficha.",
                    f"regia: {metadata.get('regia di', '')}" if metadata.get("regia di") else "",
                    f"durata: {metadata.get('durata', '')}" if metadata.get("durata") else "",
                    description,
                ]
                if value
            ),
            limit=900,
        ),
        "date": metadata.get("anno") or fallback_date,
        "embedded": False,
    }


def parse_aamod_film_post(post):
    content = _strip_html(post.get("content", {}).get("rendered", ""), limit=900)
    title = _strip_html(post.get("title", {}).get("rendered", "")) or post.get("slug", "")
    return _film_record_from_text(
        post.get("id", ""),
        title,
        post.get("link", ""),
        content,
        str(post.get("date", ""))[:10],
    )


def parse_aamod_film_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    title = _clean_text((soup.find("h1") or BeautifulSoup("", "html.parser")).get_text(" ", strip=True))
    content = _clean_text((soup.select_one("main") or soup).get_text(" ", strip=True), limit=900)
    record_id = urlparse(page_url).path.strip("/").split("/")[-1]
    return _film_record_from_text(record_id, title, page_url, content)


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": AAMOD_REPOSITORY_CODE,
        "archive_type": AAMOD_ARCHIVE_TYPE,
        "aamod_detail_url": AAMOD_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": AAMOD_HOME_URL,
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
        "partner_site": AAMOD_HOME_URL,
        "platform": record.get("platform", AAMOD_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch(url, *, stream=False):
    return SESSION.get(url, timeout=(6, REQUEST_TIMEOUT if not stream else 8), allow_redirects=True, stream=stream)


def collect_aamod_dataset():
    institutions = collect_aamod_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    catalog_errors = []

    try:
        response = _fetch(AAMOD_HOME_URL)
        response.raise_for_status()
        homepage_records = parse_aamod_home_page(response.text, response.url)
        records.extend(homepage_records)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(homepage_records),
                len(homepage_records),
                "Página inicial oficial com vídeos incorporados do canal YouTube do AAMOD.",
            )
        )
    except Exception as error:
        internal_pages.append(_internal_page_row(institution, AAMOD_HOME_URL, "erro", error=str(error)))

    for seed_url in [AAMOD_PATRIMONIO_URL, AAMOD_FAQ_URL]:
        try:
            response = _fetch(seed_url)
            response.raise_for_status()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    0,
                    0,
                    "Página institucional usada para validar patrimônio, acesso e referência ao catálogo digital.",
                )
            )
        except Exception as error:
            internal_pages.append(_internal_page_row(institution, seed_url, "erro", error=str(error)))

    try:
        response = _fetch(AAMOD_WP_FILMS_URL)
        response.raise_for_status()
        film_records = []
        for post in response.json():
            fallback_record = parse_aamod_film_post(post)
            try:
                page_response = _fetch(fallback_record["video_link"])
                page_response.raise_for_status()
                film_record = parse_aamod_film_page(page_response.text, page_response.url)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        page_response.url,
                        "ok",
                        page_response.status_code,
                        1,
                        0,
                        "Ficha pública de filme no site oficial do AAMOD; metadados coletados sem pressupor player.",
                    )
                )
            except Exception as error:
                film_record = fallback_record
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        fallback_record["video_link"],
                        "erro",
                        warning="Falha ao abrir a ficha HTML; usados metadados do endpoint WordPress.",
                        error=str(error),
                    )
                )
            film_records.append(film_record)
        records.extend(film_records)
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(film_records),
                0,
                "Endpoint WordPress público para fichas `I nostri film`; registra metadados sem pressupor player.",
            )
        )
    except Exception as error:
        internal_pages.append(_internal_page_row(institution, AAMOD_WP_FILMS_URL, "erro", error=str(error)))

    for catalog_url in AAMOD_CATALOG_URLS:
        try:
            response = _fetch(catalog_url, stream=True)
            ok = response.status_code < 400
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok" if ok else "erro",
                    response.status_code,
                    0,
                    0,
                    "Rota de catálogo digital declarada pelo AAMOD; sondada sem ingestão em massa.",
                    "" if ok else f"HTTP {response.status_code}",
                )
            )
            response.close()
        except Exception as error:
            catalog_errors.append(f"{catalog_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    catalog_url,
                    "erro",
                    warning="Rota de catálogo digital declarada pelo AAMOD, mas indisponível na sondagem simples.",
                    error=str(error),
                )
            )

    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary_status = "ok" if records else "erro"
    summary_warning = (
        "Corpus institucional incorporado por superfície oficial do AAMOD. A coleta usa vídeos incorporados "
        "na página inicial e fichas públicas do WordPress; o catálogo xDams/Archivi online foi sondado, mas "
        "não respondeu de forma estável nesta rodada. Nenhum arquivo de mídia é baixado."
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": AAMOD_HOME_URL,
            "partner_domain": normalize_domain(AAMOD_HOME_URL),
            "status": summary_status,
            "http_code": 200 if summary_status == "ok" else "",
            "integrity_status": "integro" if summary_status == "ok" else "instavel",
            "final_url": AAMOD_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "media" if embedded_total else "alta",
            "warning": summary_warning,
            "error": "; ".join(catalog_errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "AAMOD_CATALOG_URLS",
    "collect_aamod_dataset",
    "collect_aamod_institutions",
    "parse_aamod_film_page",
    "parse_aamod_film_post",
    "parse_aamod_home_page",
]
