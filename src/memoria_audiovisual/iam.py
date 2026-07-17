import html
import re
import time

import requests
from bs4 import BeautifulSoup

from .config import (
    HEADERS,
    IAM_CONSULTATION_ROOM_URL,
    IAM_HOME_URL,
    IAM_MEDIAS_API_URL,
    IAM_MEDIAS_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


IAM_REPOSITORY_CODE = "MC-IAM"
IAM_ARCHIVE_TYPE = "Institutional audiovisual archive"
IAM_COUNTRY = normalize_country("Monaco")
IAM_INSTITUTION_NAME = "Institut audiovisuel de Monaco"
IAM_PLATFORM_LABEL = "Institut audiovisuel de Monaco"
IAM_WP_PER_PAGE = 100
IAM_REQUEST_PAUSE = 0.1

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


def collect_iam_institutions():
    return [
        {
            "institution": IAM_INSTITUTION_NAME,
            "slug": slugify(IAM_INSTITUTION_NAME),
            "country": IAM_COUNTRY,
            "continent": country_to_continent(IAM_COUNTRY),
            "repository_code": IAM_REPOSITORY_CODE,
            "archive_type": IAM_ARCHIVE_TYPE,
            "iam_detail_url": IAM_HOME_URL,
            "external_url": IAM_HOME_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def _class_terms(post, prefix):
    terms = []
    for class_name in post.get("class_list") or []:
        if not str(class_name).startswith(prefix):
            continue
        label = str(class_name)[len(prefix) :].replace("-", " ").strip()
        if label:
            terms.append(label)
    return ", ".join(sorted(dict.fromkeys(terms)))


def _extract_video_source(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    source = soup.find("source", src=True)
    if source:
        return source.get("src", ""), source.get("type", "")
    video = soup.find("video", src=True)
    if video:
        return video.get("src", ""), video.get("type", "")
    return "", ""


def _extract_page_description(html_text):
    soup = BeautifulSoup(html_text or "", "html.parser")
    article = soup.find("article") or soup.find("main") or soup
    for tag in article.find_all(["script", "style", "nav", "header", "footer", "iframe"]):
        tag.decompose()
    return _clean_text(article.get_text(" ", strip=True), limit=900)


def _extract_year(*values):
    text = " ".join(str(value or "") for value in values)
    match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    return match.group(1) if match else ""


def parse_iam_media_post(post, detail_html=""):
    title = _strip_html(post.get("title", {}).get("rendered", "")) or str(post.get("slug", ""))
    page_url = post.get("link", "")
    video_source, video_type = _extract_video_source(detail_html)
    description = _extract_page_description(detail_html)
    fonds = _class_terms(post, "fonds-")
    categories = _class_terms(post, "medias-categorie-")
    keywords = _class_terms(post, "mots-cles-")
    places = _class_terms(post, "lieux-")
    authors = _class_terms(post, "auteurs-")
    periods = _class_terms(post, "periode-")
    supports = _class_terms(post, "supports-")
    document_types = _class_terms(post, "types-de-documents-")
    technical = _class_terms(post, "specificites-techniques-")
    year = _extract_year(periods, description, post.get("date", ""))
    note = _clean_text(
        " | ".join(
            value
            for value in [
                "Registro público do tipo WordPress `medias` do Institut audiovisuel de Monaco.",
                f"fundo: {fonds}" if fonds else "",
                f"categoria: {categories}" if categories else "",
                f"palavras-chave: {keywords}" if keywords else "",
                f"lugares: {places}" if places else "",
                f"autores: {authors}" if authors else "",
                f"período: {periods}" if periods else "",
                f"suporte: {supports}" if supports else "",
                f"tipo: {document_types}" if document_types else "",
                f"técnica: {technical}" if technical else "",
                f"fonte de vídeo: {video_type}" if video_type else "",
                description,
            ]
            if value
        ),
        limit=1000,
    )
    return {
        "record_id": str(post.get("id", "")),
        "source_kind": "wordpress_medias",
        "video_link": video_source or page_url,
        "page_url": page_url,
        "platform": IAM_PLATFORM_LABEL,
        "title": title,
        "subject": categories or document_types or keywords,
        "description": note,
        "date": year or str(post.get("date", ""))[:10],
        "embedded": bool(video_source),
    }


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": IAM_REPOSITORY_CODE,
        "archive_type": IAM_ARCHIVE_TYPE,
        "iam_detail_url": IAM_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": IAM_MEDIAS_API_URL,
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
        "partner_site": IAM_MEDIAS_API_URL,
        "platform": record.get("platform", IAM_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _fetch_media_page(page):
    response = _fetch(
        IAM_MEDIAS_API_URL,
        params={
            "per_page": IAM_WP_PER_PAGE,
            "page": page,
            "_fields": "id,date,modified,slug,title,link,class_list",
        },
    )
    response.raise_for_status()
    return response


def collect_iam_dataset():
    institutions = collect_iam_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    page_errors = []
    api_errors = []
    total_expected = 0
    total_pages = 1

    for url, warning in [
        (IAM_HOME_URL, "Site institucional do Institut audiovisuel de Monaco."),
        (
            IAM_CONSULTATION_ROOM_URL,
            "Página da sala de consulta: confirma acervo muito maior que o recorte online coletado.",
        ),
        (IAM_MEDIAS_API_URL, "Endpoint público WordPress `medias`, usado como rota catalográfica online."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, 0, 0, warning))
        except Exception as error:
            page_errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    page = 1
    while page <= total_pages:
        try:
            response = _fetch_media_page(page)
            if page == 1:
                total_expected = _as_int(response.headers.get("X-WP-Total"))
                total_pages = _as_int(response.headers.get("X-WP-TotalPages"), 1)
            posts = response.json()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(posts),
                    0,
                    f"Página {page} de {total_pages} do endpoint WordPress público `medias`.",
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
                            "Página pública `/medias/`; player HTML verificado sem baixar mídia.",
                        )
                    )
                except Exception as error:
                    page_errors.append(f"{post.get('link', '')}: {error}")
                    internal_pages.append(
                        _internal_page_row(
                            institution,
                            post.get("link", ""),
                            "erro",
                            warning="Falha ao abrir página individual `/medias/`.",
                            error=str(error),
                        )
                    )
                records.append(parse_iam_media_post(post, detail_html))
        except Exception as error:
            api_errors.append(f"medias page {page}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    f"{IAM_MEDIAS_API_URL}?per_page={IAM_WP_PER_PAGE}&page={page}",
                    "erro",
                    warning="Falha em página do endpoint `medias`; completude da rodada fica parcial.",
                    error=str(error),
                )
            )
        page += 1
        if page <= total_pages:
            time.sleep(IAM_REQUEST_PAUSE)

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_endpoint = bool(total_expected) and len(video_links) == total_expected and not api_errors
    embedded_total = sum(1 for record in records if record.get("embedded"))
    summary_warning = (
        "Corpus institucional incorporado pelo endpoint público WordPress `medias` do Institut audiovisuel de Monaco. "
        f"A rodada materializou {len(video_links)} de {total_expected or len(video_links)} registros declarados pelo endpoint, "
        f"com {embedded_total} páginas contendo fonte de vídeo detectada. "
        "O recorte online não equivale ao acervo total declarado pela sala de consulta."
    )
    if not complete_endpoint:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha ou divergência de paginação."

    summary = [
        {
            **_base_row(institution),
            "partner_site": IAM_MEDIAS_API_URL,
            "partner_domain": normalize_domain(IAM_HOME_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_endpoint else "acessivel" if video_links else "instavel",
            "final_url": IAM_MEDIAS_API_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_endpoint else "media",
            "warning": summary_warning,
            "error": "; ".join([*page_errors, *api_errors]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "IAM_WP_PER_PAGE",
    "collect_iam_dataset",
    "collect_iam_institutions",
    "parse_iam_media_post",
]
