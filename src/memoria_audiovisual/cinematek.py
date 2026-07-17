import re
import time
from urllib.parse import unquote, urlparse

import requests

from .config import CINEMATEK_BE_FILM_URL, CINEMATEK_FILM_COLLECTION_URL, CINEMATEK_HOME_URL, HEADERS, REQUEST_TIMEOUT
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMATEK_REPOSITORY_CODE = "BE-CINEMATEK"
CINEMATEK_ARCHIVE_TYPE = "National cinematheque and external streaming access routes"
CINEMATEK_COUNTRY = normalize_country("Belgium")
CINEMATEK_INSTITUTION_NAME = "Cinémathèque royale de Belgique / CINEMATEK"
CINEMATEK_PLATFORM_LABEL = "CINEMATEK@HOME"

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,nl;q=0.7,pt-BR;q=0.6"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch(url):
    response = None
    for attempt in range(4):
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        if response.status_code not in {429, 503}:
            return response
        time.sleep(1.2 * (attempt + 1))
    return response


def _title_from_external_url(url):
    parsed = urlparse(str(url or ""))
    path = unquote(parsed.path.strip("/"))
    if "avilafilm.be" in parsed.netloc and path.startswith("en/film/"):
        slug = path.split("/en/film/")[-1] if "/en/film/" in path else path.split("/")[-1]
    elif "stream.sooner.be" in parsed.netloc:
        match = re.search(r"/m/([^/?#]+)", parsed.path)
        slug = match.group(1) if match else path.split("/")[-1]
    else:
        slug = path.split("/")[-1]
    return _clean_text(slug.replace("-", " ").replace("%20", " ").title())


def _platform_from_url(url):
    host = urlparse(str(url or "")).netloc.lower()
    if "avila" in host:
        return "Avila"
    if "sooner" in host:
        return "Sooner"
    if "lumiere" in host or "lumière" in host:
        return "Lumière"
    return "Plataforma externa"


def collect_cinematek_institutions():
    return [
        {
            "institution": CINEMATEK_INSTITUTION_NAME,
            "slug": slugify(CINEMATEK_INSTITUTION_NAME),
            "country": CINEMATEK_COUNTRY,
            "continent": country_to_continent(CINEMATEK_COUNTRY),
            "repository_code": CINEMATEK_REPOSITORY_CODE,
            "archive_type": CINEMATEK_ARCHIVE_TYPE,
            "cinematek_detail_url": CINEMATEK_FILM_COLLECTION_URL,
            "external_url": CINEMATEK_BE_FILM_URL,
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
        "repository_code": CINEMATEK_REPOSITORY_CODE,
        "archive_type": CINEMATEK_ARCHIVE_TYPE,
        "cinematek_detail_url": CINEMATEK_FILM_COLLECTION_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMATEK_BE_FILM_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cinematek_home_links(html_text, page_url=CINEMATEK_BE_FILM_URL):
    records = []
    seen = set()
    for match in re.finditer(r'href="(https?://(?:www\.)?(?:avilafilm\.be/en/film|stream\.sooner\.be/search)[^"]+)"', html_text or "", re.I):
        url = match.group(1).replace("&amp;", "&")
        if url in seen:
            continue
        seen.add(url)
        external_platform = _platform_from_url(url)
        title = _title_from_external_url(url)
        records.append(
            {
                "record_id": f"{external_platform.lower()}:{urlparse(url).path.strip('/')}",
                "source_kind": "cinematek_home_external_streaming_route",
                "page_url": page_url,
                "video_link": url,
                "platform": CINEMATEK_PLATFORM_LABEL,
                "title": title,
                "subject": f"CINEMATEK@HOME; {external_platform}",
                "description": _clean_text(
                    "Rota oficial CINEMATEK@HOME para filme restaurado em plataforma externa. "
                    f"Acesso mediado por {external_platform}; sinais de assinatura, aluguel, compra ou login "
                    "devem ser tratados como restrição/autenticação, não como acervo aberto direto.",
                    limit=1000,
                ),
                "date": "",
                "embedded": False,
            }
        )
    return records


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CINEMATEK_BE_FILM_URL,
        "platform": CINEMATEK_PLATFORM_LABEL,
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_cinematek_dataset():
    institutions = collect_cinematek_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    errors = []

    for url, warning in [
        (CINEMATEK_HOME_URL, "Site institucional da Cinémathèque royale de Belgique / CINEMATEK."),
        (CINEMATEK_FILM_COLLECTION_URL, "Página oficial de coleções fílmicas; distingue acervo, pesquisa e acesso sob demanda."),
        (CINEMATEK_BE_FILM_URL, "Rota pública CINEMATEK@HOME; lista filmes restaurados em plataformas externas."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            page_records = parse_cinematek_home_links(response.text, response.url) if url == CINEMATEK_BE_FILM_URL else []
            for record in page_records:
                records_by_id[record["record_id"]] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    0,
                    warning,
                )
            )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEMATEK_BE_FILM_URL,
            "partner_domain": normalize_domain(CINEMATEK_BE_FILM_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CINEMATEK_BE_FILM_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus incorporado pelo recorte CINEMATEK@HOME: a página oficial lista filmes "
                f"restaurados em plataformas externas. O MVP materializa {len(records)} rotas de acesso "
                "externas, sem baixar mídia e sem afirmar acesso aberto direto ou cobertura total do acervo "
                "preservado da Cinémathèque royale de Belgique."
            ),
            "error": " | ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMATEK_ARCHIVE_TYPE",
    "CINEMATEK_COUNTRY",
    "CINEMATEK_INSTITUTION_NAME",
    "CINEMATEK_PLATFORM_LABEL",
    "CINEMATEK_REPOSITORY_CODE",
    "collect_cinematek_dataset",
    "collect_cinematek_institutions",
    "parse_cinematek_home_links",
]
