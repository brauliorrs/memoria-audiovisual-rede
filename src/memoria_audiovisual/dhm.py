from __future__ import annotations

import re
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import (
    DHM_EFG_PAGE_URL,
    DHM_FILM_ARCHIVE_URL,
    DHM_HOME_URL,
    DHM_MARSHALL_PLAN_URL,
    DHM_ZEUGHAUSKINO_HOME_URL,
    DHM_ZEUGHAUSKINO_ONLINE_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


DHM_REPOSITORY_CODE = "DE-DHM"
DHM_ARCHIVE_TYPE = "Museum film archive with public descriptive online film selection"
DHM_COUNTRY = normalize_country("Germany")
DHM_INSTITUTION_NAME = "Deutsches Historisches Museum / Zeughauskino"
DHM_PLATFORM_LABEL = "DHM Zeughauskino online"
DHM_REQUEST_PAUSE = 0.1

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en,de;q=0.8,pt-BR;q=0.7",
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


def _extract_year(text):
    match = re.search(r"\b((?:18|19|20)\d{2}(?:[–-]\d{2})?)\b", str(text or ""))
    return match.group(1) if match else ""


def _detail_url_from_article(article, page_url):
    anchor = article.select_one(
        'a[href*="/films-of-the-marshall-plan/"], '
        'a[href*="/filme-des-marshall-plans/"]'
    )
    if not anchor:
        return ""
    href = _clean_text(anchor.get("href", ""))
    if not href:
        return ""
    detail_url = urljoin(page_url, href)
    if detail_url.rstrip("/") == page_url.rstrip("/"):
        return ""
    return detail_url


def _record_id_from_url(url, title):
    parsed = urlparse(str(url or ""))
    if parsed.fragment:
        return f"marshall-plan-{parsed.fragment}"
    slug = parsed.path.rstrip("/").rsplit("/", 1)[-1]
    return slug or f"marshall-plan-{slugify(title)}"


def _image_or_media_source_count(soup):
    count = len(soup.find_all("video"))
    for iframe in soup.find_all("iframe"):
        src = _clean_text(iframe.get("src", "")).lower()
        if any(marker in src for marker in ("youtube", "vimeo", "player", "video")):
            count += 1
    for source in soup.find_all("source"):
        src = _clean_text(source.get("src") or source.get("data-src") or source.get("srcset") or "")
        source_type = _clean_text(source.get("type", "")).lower()
        if source.find_parent("video") or source_type.startswith("video/") or src.lower().endswith(
            (".mp4", ".m3u8", ".webm", ".mov", ".m4v")
        ):
            count += 1
    return count


def parse_dhm_marshall_plan_page(html, page_url=DHM_MARSHALL_PLAN_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    records = []
    seen = set()

    for article in soup.select("article.grid-teaser__content-wrapper"):
        title_node = article.find("h3")
        title = _clean_text(title_node.get_text(" ", strip=True) if title_node else "")
        if not title:
            continue
        metadata_node = article.select_one(".grid-teaser__infobox p")
        metadata = _clean_text(metadata_node.get_text(" ", strip=True) if metadata_node else "")
        detail_url = _detail_url_from_article(article, page_url)
        record_url = detail_url or f"{page_url.rstrip('/')}#{slugify(title)}"
        record_id = _record_id_from_url(record_url, title)
        if record_id in seen:
            continue
        seen.add(record_id)
        has_detail = bool(detail_url)
        records.append(
            {
                "record_id": record_id,
                "source_kind": "marshall_plan_detail" if has_detail else "marshall_plan_index",
                "video_link": record_url,
                "page_url": record_url,
                "detail_url": detail_url,
                "platform": DHM_PLATFORM_LABEL,
                "title": title,
                "subject": metadata,
                "description": _clean_text(
                    " | ".join(
                        value
                        for value in [
                            "Registro descritivo público da seleção online Films of the Marshall Plan do DHM/Zeughauskino; ficha audiovisual sem player aberto detectado.",
                            "ficha individual pública disponível" if has_detail else "item descrito diretamente na listagem pública, sem ficha individual linkada",
                            metadata,
                        ]
                        if value
                    ),
                    limit=1000,
                ),
                "date": _extract_year(metadata),
                "embedded": False,
                "detail_available": has_detail,
            }
        )
    return records


DETAIL_FIELD_ALIASES = {
    "other title": "other_title",
    "other titles": "other_title",
    "produced by": "produced_by",
    "directed by": "directed_by",
    "country/year": "country_year",
    "length": "duration",
    "language": "language",
    "format": "format",
}


def _normalize_detail_label(value):
    return _clean_text(value).rstrip(":").strip().lower()


def _extract_detail_fields(lines):
    fields = {}
    for index, line in enumerate(lines[:-1]):
        key = DETAIL_FIELD_ALIASES.get(_normalize_detail_label(line))
        if key and not fields.get(key):
            fields[key] = _clean_text(lines[index + 1])
    return fields


def parse_dhm_detail_page(html, page_url, fallback=None):
    fallback = fallback or {}
    soup = BeautifulSoup(html or "", "html.parser")
    main = soup.select_one("main") or soup
    lines = [_clean_text(line) for line in main.get_text("\n", strip=True).splitlines()]
    lines = [line for line in lines if line]
    title_node = main.find("h1")
    title = _clean_text(title_node.get_text(" ", strip=True) if title_node else fallback.get("title", ""))
    fields = _extract_detail_fields(lines)

    start_index = 0
    title_positions = [index for index, line in enumerate(lines) if title and line == title]
    if title_positions:
        start_index = title_positions[-1] + 1
    field_positions = [
        index
        for index, line in enumerate(lines)
        if _normalize_detail_label(line) in DETAIL_FIELD_ALIASES
    ]
    if field_positions:
        start_index = min(field_positions)

    detail_text = _clean_text(" | ".join(lines[start_index:]), limit=1500)
    subject_parts = [
        fields.get("country_year"),
        f"direção: {fields['directed_by']}" if fields.get("directed_by") else "",
        f"produção: {fields['produced_by']}" if fields.get("produced_by") else "",
    ]
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública do DHM/Zeughauskino para a seleção Films of the Marshall Plan; metadados filmográficos sem player aberto detectado.",
                detail_text or fallback.get("description", ""),
            ]
            if value
        ),
        limit=1800,
    )
    return {
        "record_id": _record_id_from_url(page_url, title or fallback.get("title", "")),
        "source_kind": "marshall_plan_detail",
        "video_link": page_url,
        "page_url": page_url,
        "detail_url": page_url,
        "platform": DHM_PLATFORM_LABEL,
        "title": title or fallback.get("title", ""),
        "subject": _clean_text("; ".join(part for part in subject_parts if part)) or fallback.get("subject", ""),
        "description": description or fallback.get("description", ""),
        "date": _extract_year(fields.get("country_year") or detail_text) or fallback.get("date", ""),
        "duration": fields.get("duration", ""),
        "language": fields.get("language", ""),
        "format": fields.get("format", ""),
        "embedded": bool(_image_or_media_source_count(main)),
        "detail_available": True,
    }


def collect_dhm_institutions():
    return [
        {
            "institution": DHM_INSTITUTION_NAME,
            "slug": slugify("deutsches-historisches-museum-zeughauskino"),
            "country": DHM_COUNTRY,
            "continent": country_to_continent(DHM_COUNTRY),
            "repository_code": DHM_REPOSITORY_CODE,
            "archive_type": DHM_ARCHIVE_TYPE,
            "dhm_detail_url": DHM_MARSHALL_PLAN_URL,
            "external_url": DHM_HOME_URL,
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
        "repository_code": DHM_REPOSITORY_CODE,
        "archive_type": DHM_ARCHIVE_TYPE,
        "dhm_detail_url": DHM_MARSHALL_PLAN_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": DHM_MARSHALL_PLAN_URL,
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
        "partner_site": DHM_MARSHALL_PLAN_URL,
        "platform": DHM_PLATFORM_LABEL,
        "video_link": record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_dhm_dataset():
    institutions = collect_dhm_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []

    for url, warning in [
        (DHM_HOME_URL, "Site institucional do Deutsches Historisches Museum."),
        (DHM_ZEUGHAUSKINO_HOME_URL, "Superfície institucional do Zeughauskino."),
        (DHM_FILM_ARCHIVE_URL, "Página institucional do Film Archive do DHM; informa arquivo fílmico e acesso para pesquisa."),
        (DHM_ZEUGHAUSKINO_ONLINE_URL, "Página Zeughauskino online; indica coleção Films of the Marshall Plan."),
        (DHM_EFG_PAGE_URL, "Página do EFG usada apenas como evidência de identificação institucional, não como rota de corpus."),
    ]:
        try:
            response = _fetch(url)
            internal_pages.append(_internal_page_row(institution, response.url, "ok", response.status_code, warning=warning))
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    try:
        response = _fetch(DHM_MARSHALL_PLAN_URL)
        listed_records = parse_dhm_marshall_plan_page(response.text, response.url)
        embedded_count = _image_or_media_source_count(BeautifulSoup(response.text, "html.parser"))
        internal_pages.append(
            _internal_page_row(
                institution,
                response.url,
                "ok",
                response.status_code,
                len(listed_records),
                embedded_count,
                "Listagem pública The Films materializada integralmente; tags source da página são imagens, não player.",
            )
        )
    except Exception as error:
        listed_records = []
        errors.append(f"{DHM_MARSHALL_PLAN_URL}: {error}")
        internal_pages.append(
            _internal_page_row(
                institution,
                DHM_MARSHALL_PLAN_URL,
                "erro",
                warning="Falha ao abrir a seleção Films of the Marshall Plan.",
                error=str(error),
            )
        )

    records_by_id = {record["record_id"]: record for record in listed_records}
    for listed_record in listed_records:
        detail_url = listed_record.get("detail_url", "")
        if not detail_url:
            continue
        try:
            response = _fetch(detail_url)
            record = parse_dhm_detail_page(response.text, response.url, listed_record)
            records_by_id[listed_record["record_id"]] = record
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    1 if record.get("embedded") else 0,
                    "Ficha individual pública verificada; nenhum player aberto detectado.",
                )
            )
        except Exception as error:
            errors.append(f"{detail_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_url,
                    "erro",
                    0,
                    1,
                    0,
                    "Falha ao abrir ficha individual; registro mantido pela listagem pública.",
                    str(error),
                )
            )
        time.sleep(DHM_REQUEST_PAUSE)

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records if record.get("page_url")]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    detail_total = sum(1 for record in records if record.get("detail_available"))
    summary = [
        {
            **_base_row(institution),
            "partner_site": DHM_MARSHALL_PLAN_URL,
            "partner_domain": normalize_domain(DHM_MARSHALL_PLAN_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if video_links else "instavel",
            "final_url": DHM_MARSHALL_PLAN_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if video_links else "alta",
            "warning": (
                "Corpus DHM/Zeughauskino incorporado pela seleção pública Films of the Marshall Plan. "
                f"A rota materializa {len(video_links)} registros filmográficos públicos, {detail_total} com ficha individual "
                f"e {embedded_total} sinais de player. A página institucional informa 42 filmes do Plano Marshall no acervo, "
                "mas a listagem pública coletável nesta rodada expõe uma seleção de 34 itens; o corpus não representa o Film Archive integral e não baixa mídia."
            ),
            "error": "; ".join(errors[:5]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "DHM_ARCHIVE_TYPE",
    "DHM_INSTITUTION_NAME",
    "DHM_PLATFORM_LABEL",
    "DHM_REPOSITORY_CODE",
    "collect_dhm_dataset",
    "collect_dhm_institutions",
    "parse_dhm_detail_page",
    "parse_dhm_marshall_plan_page",
]
