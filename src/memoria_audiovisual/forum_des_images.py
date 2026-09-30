import re
import time
from urllib.parse import parse_qs, urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from .config import (
    FORUM_DES_IMAGES_BROWSE_URL,
    FORUM_DES_IMAGES_DETAILS_URL_TEMPLATE,
    FORUM_DES_IMAGES_FILMS_AMATEURS_URL,
    FORUM_DES_IMAGES_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


FORUM_DES_IMAGES_REPOSITORY_CODE = "FR-FORUM-DES-IMAGES"
FORUM_DES_IMAGES_ARCHIVE_TYPE = "Public audiovisual collection and film documentation centre"
FORUM_DES_IMAGES_COUNTRY = normalize_country("France")
FORUM_DES_IMAGES_INSTITUTION_NAME = "Forum des images"
FORUM_DES_IMAGES_PLATFORM_LABEL = "Collections du Forum des images"
FORUM_DES_IMAGES_MAX_BROWSE_PAGES = 4
FORUM_DES_IMAGES_MAX_DETAIL_PAGES = 30

_FALLBACK_BROWSE_URLS = (
    f'{FORUM_DES_IMAGES_BROWSE_URL}?query=%22Jean-Luc+Godard%22',
    f"{FORUM_DES_IMAGES_BROWSE_URL}?query=prix+clermont+ferrand",
    (
        f"{FORUM_DES_IMAGES_BROWSE_URL}"
        "?facetClause=%2BGenreFacet%3Afiction%3B&profile="
        "&query=film+burlesque&sort=title_sort_ASC%3BchildOrder_sort_ASC"
    ),
)

SESSION = requests.Session()
SESSION.headers.update(
    {
        **HEADERS,
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8,pt-BR;q=0.7",
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
        response = SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
        if response.status_code not in {429, 503}:
            return response
        time.sleep(1.2 * (attempt + 1))
    return response


def _robots_allowed(url):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    try:
        response = SESSION.get(robots_url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)
    except requests.RequestException:
        return False, "robots_unreachable"
    if response.status_code in {404, 410}:
        return True, "robots_absent"
    if response.status_code != 200:
        return False, f"robots_http_{response.status_code}"
    parser = RobotFileParser()
    parser.set_url(response.url)
    parser.parse(response.text.splitlines())
    user_agent = SESSION.headers.get("User-Agent", "*")
    return parser.can_fetch(user_agent, url), "robots_evaluated"


def _record_id_from_url(url):
    query = parse_qs(urlparse(str(url or "")).query)
    return _clean_text((query.get("id") or [""])[0])


def _extract_year(text):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(text or ""))
    return match.group(1) if match else ""


def _extract_declared_collection_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(
        r"(?:fonds|collections?).{0,80}?(?:plus\s+de\s+)?([\d\s\u00a0]+)\s+films",
        text,
        re.I,
    )
    if not match:
        match = re.search(r"plus\s+de\s+([\d\s\u00a0]+)\s+films", text, re.I)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def _extract_result_total(html_text):
    text = BeautifulSoup(html_text or "", "html.parser").get_text(" ", strip=True)
    match = re.search(r"([\d\s\u00a0]+)\s+r[ée]sultats?\s+dans", text, re.I)
    return int(re.sub(r"\D", "", match.group(1)) or 0) if match else 0


def _extract_browse_links(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    seen = set()
    for anchor in soup.find_all("a", href=True):
        href = urljoin(page_url, anchor.get("href", ""))
        if "/CogniTellUI/faces/browse.xhtml" not in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        links.append(href)
    return links


def _availability_from_text(text):
    normalized = _clean_text(text).lower()
    if (
        "visible sur internet" in normalized
        or "visible en salle des collections et sur internet" in normalized
    ):
        return "visible_sur_internet"
    if (
        "n'est pas visible" in normalized
        or "non visible" in normalized
        or "non visionnable" in normalized
    ):
        return "non_visible_en_ligne"
    if "visible en salle des collections" in normalized:
        return "consultation_sur_place"
    return "non_documente"


def parse_forum_des_images_browse_page(html_text, page_url=FORUM_DES_IMAGES_BROWSE_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for anchor in soup.find_all("a", href=re.compile(r"details\.xhtml\?id=", re.I)):
        detail_url = urljoin(page_url, anchor.get("href", ""))
        record_id = _record_id_from_url(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        container = (
            anchor.find_parent("li")
            or anchor.find_parent("article")
            or anchor.find_parent("tr")
            or anchor.find_parent("div")
            or anchor.parent
        )
        container_text = _clean_text(
            container.get_text(" ", strip=True) if container else anchor.get_text(" ", strip=True),
            limit=1800,
        )
        title = _clean_text(anchor.get_text(" ", strip=True), limit=300)
        if not title:
            title = _clean_text(anchor.get("title"), limit=300)
        records.append(
            {
                "record_id": record_id,
                "page_url": detail_url,
                "title": title,
                "date": _extract_year(container_text),
                "availability": _availability_from_text(container_text),
                "browse_context": container_text,
            }
        )
    return records


def _detail_fields(soup):
    fields = {}
    for row in soup.find_all("tr"):
        cells = [_clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        if len(cells) >= 2 and cells[0]:
            fields[cells[0].rstrip(":").lower()] = _clean_text(" ".join(cells[1:]), limit=1000)
    for term in soup.find_all("dt"):
        desc = term.find_next_sibling("dd")
        if desc:
            fields[_clean_text(term.get_text(" ", strip=True)).rstrip(":").lower()] = _clean_text(
                desc.get_text(" ", strip=True), limit=1000
            )
    return fields


def parse_forum_des_images_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    page_text = _clean_text(soup.get_text(" ", strip=True), limit=6000)
    record_id = _record_id_from_url(page_url)
    heading = soup.find("h1") or soup.find("h2")
    title = _clean_text(heading.get_text(" ", strip=True) if heading else "", limit=300)
    if not title:
        title = _clean_text((soup.find("title") or "").get_text(" ", strip=True), limit=300)
    fields = _detail_fields(soup)
    creator = ""
    for key in ("réalisation", "realisation", "réalisateur", "realisateur"):
        if fields.get(key):
            creator = fields[key]
            break
    if not creator:
        match = re.search(r"\bde\s+([^|]{2,120}?)(?=\s+(?:fiction|documentaire|retransmission|19\d{2}|20\d{2})\b)", page_text, re.I)
        creator = _clean_text(match.group(1), limit=250) if match else ""
    collection = ""
    match = re.search(r"\bcollection\s+([^|]{2,180}?)(?=\s+(?:Générique|Infos techniques|Pour aller plus loin|$))", page_text, re.I)
    if match:
        collection = _clean_text(match.group(1), limit=250)
    availability = _availability_from_text(page_text)
    media_urls = []
    for tag in soup.find_all(["video", "source", "iframe", "a"], href=True):
        candidate = tag.get("src") or tag.get("href")
        if candidate and re.search(r"\.(?:mp4|m3u8|webm)(?:\?|$)|youtube|vimeo", candidate, re.I):
            media_urls.append(urljoin(page_url, candidate))
    for tag in soup.find_all(["video", "source", "iframe"], src=True):
        candidate = tag.get("src")
        if candidate and candidate not in media_urls:
            if re.search(r"\.(?:mp4|m3u8|webm)(?:\?|$)|youtube|vimeo|player", candidate, re.I):
                media_urls.append(urljoin(page_url, candidate))
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública do catálogo Collections du Forum des images.",
                f"disponibilidade: {availability}",
                f"realização: {creator}" if creator else "",
                f"collection: {collection}" if collection else "",
                page_text,
            ]
            if value
        ),
        limit=2000,
    )
    return {
        "record_id": record_id,
        "source_kind": "forum_des_images_detail_record",
        "page_url": page_url,
        "video_link": media_urls[0] if media_urls else page_url,
        "platform": FORUM_DES_IMAGES_PLATFORM_LABEL,
        "title": title,
        "subject": "; ".join(value for value in [creator, collection] if value),
        "description": description,
        "date": _extract_year(page_text),
        "embedded": bool(media_urls),
        "availability": availability,
    }


def collect_forum_des_images_institutions():
    return [
        {
            "institution": FORUM_DES_IMAGES_INSTITUTION_NAME,
            "slug": slugify(FORUM_DES_IMAGES_INSTITUTION_NAME),
            "country": FORUM_DES_IMAGES_COUNTRY,
            "continent": country_to_continent(FORUM_DES_IMAGES_COUNTRY),
            "repository_code": FORUM_DES_IMAGES_REPOSITORY_CODE,
            "archive_type": FORUM_DES_IMAGES_ARCHIVE_TYPE,
            "forum_des_images_detail_url": FORUM_DES_IMAGES_HOME_URL,
            "external_url": FORUM_DES_IMAGES_HOME_URL,
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
        "repository_code": FORUM_DES_IMAGES_REPOSITORY_CODE,
        "archive_type": FORUM_DES_IMAGES_ARCHIVE_TYPE,
        "forum_des_images_detail_url": FORUM_DES_IMAGES_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": FORUM_DES_IMAGES_HOME_URL,
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
        "partner_site": FORUM_DES_IMAGES_HOME_URL,
        "platform": FORUM_DES_IMAGES_PLATFORM_LABEL,
        "video_link": record.get("video_link") or record.get("page_url", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description")
        or _clean_text(
            " | ".join(
                value
                for value in [
                    "Registro público do catálogo Collections du Forum des images.",
                    f"disponibilidade: {record.get('availability', 'non_documente')}",
                    record.get("browse_context", ""),
                ]
                if value
            ),
            limit=1800,
        ),
        "video_published_at": record.get("date", ""),
    }


def collect_forum_des_images_dataset():
    institutions = collect_forum_des_images_institutions()
    institution = institutions[0]
    internal_pages = []
    errors = []
    records_by_id = {}
    browse_urls = []
    declared_collection_total = 0
    declared_result_total_max = 0

    for source_url, label in (
        (FORUM_DES_IMAGES_HOME_URL, "Página inicial do catálogo público."),
        (FORUM_DES_IMAGES_FILMS_AMATEURS_URL, "Coleção temática oficial Films amateurs."),
    ):
        allowed, robots_status = _robots_allowed(source_url)
        if not allowed:
            errors.append(f"{source_url}: blocked by robots ({robots_status})")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    source_url,
                    "bloqueado_robots",
                    warning=label,
                    error=robots_status,
                )
            )
            continue
        try:
            response = _fetch(source_url)
            response.raise_for_status()
            declared_collection_total = max(
                declared_collection_total,
                _extract_declared_collection_total(response.text),
            )
            browse_urls.extend(_extract_browse_links(response.text, response.url))
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    warning=f"{label} robots={robots_status}",
                )
            )
        except Exception as error:
            errors.append(f"{source_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    source_url,
                    "erro",
                    warning=label,
                    error=str(error),
                )
            )

    browse_urls.extend(_FALLBACK_BROWSE_URLS)
    ordered_browse = []
    seen_browse = set()
    for url in browse_urls:
        if url not in seen_browse:
            seen_browse.add(url)
            ordered_browse.append(url)
    ordered_browse = ordered_browse[:FORUM_DES_IMAGES_MAX_BROWSE_PAGES]

    for browse_url in ordered_browse:
        allowed, robots_status = _robots_allowed(browse_url)
        if not allowed:
            errors.append(f"{browse_url}: blocked by robots ({robots_status})")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    browse_url,
                    "bloqueado_robots",
                    warning="Rota de busca pública.",
                    error=robots_status,
                )
            )
            continue
        try:
            response = _fetch(browse_url)
            response.raise_for_status()
            page_records = parse_forum_des_images_browse_page(response.text, response.url)
            declared_result_total_max = max(
                declared_result_total_max,
                _extract_result_total(response.text),
            )
            for record in page_records:
                records_by_id.setdefault(record["record_id"], record)
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    len(page_records),
                    warning=(
                        "Rota pública de busca/faceta do catálogo; "
                        f"robots={robots_status}."
                    ),
                )
            )
        except Exception as error:
            errors.append(f"{browse_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    browse_url,
                    "erro",
                    warning="Falha ao abrir rota pública de busca/faceta.",
                    error=str(error),
                )
            )

    for record in list(records_by_id.values())[:FORUM_DES_IMAGES_MAX_DETAIL_PAGES]:
        detail_url = FORUM_DES_IMAGES_DETAILS_URL_TEMPLATE.format(
            record_id=record["record_id"]
        )
        allowed, robots_status = _robots_allowed(detail_url)
        if not allowed:
            errors.append(f"{detail_url}: blocked by robots ({robots_status})")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_url,
                    "bloqueado_robots",
                    warning="Ficha pública de item.",
                    error=robots_status,
                )
            )
            continue
        try:
            response = _fetch(detail_url)
            response.raise_for_status()
            parsed = parse_forum_des_images_detail_page(response.text, response.url)
            if parsed["record_id"] in records_by_id:
                list_title = records_by_id[parsed["record_id"]].get("title", "")
                records_by_id[parsed["record_id"]].update(parsed)
                if list_title and not records_by_id[parsed["record_id"]].get("title"):
                    records_by_id[parsed["record_id"]]["title"] = list_title
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok",
                    response.status_code,
                    1,
                    1 if parsed.get("embedded") else 0,
                    warning=f"Ficha pública de item; robots={robots_status}.",
                )
            )
        except Exception as error:
            errors.append(f"{detail_url}: {error}")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    detail_url,
                    "erro",
                    warning="Falha ao abrir ficha pública de item.",
                    error=str(error),
                )
            )

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    visible_online = sum(
        1 for record in records if record.get("availability") == "visible_sur_internet"
    )
    summary = [
        {
            **_base_row(institution),
            "partner_site": FORUM_DES_IMAGES_HOME_URL,
            "partner_domain": normalize_domain(FORUM_DES_IMAGES_HOME_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": FORUM_DES_IMAGES_HOME_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": sum(
                1 for record in records if record.get("embedded")
            ),
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": _clean_text(
                "Corpus institucional incorporado a partir do catálogo público "
                "Collections du Forum des images. A instituição declara fundo superior "
                f"a {declared_collection_total or 8000} filmes; a rodada observa até "
                f"{FORUM_DES_IMAGES_MAX_BROWSE_PAGES} rotas oficiais de busca/faceta e "
                f"até {FORUM_DES_IMAGES_MAX_DETAIL_PAGES} fichas. O maior conjunto de "
                f"resultados declarado nas sementes foi {declared_result_total_max or 'não determinado'}; "
                f"{visible_online} registros da amostra foram marcados como visíveis na internet. "
                "O corpus representa metadados públicos materializados e não afirma cobertura "
                "total do acervo nem disponibilidade online integral dos filmes."
            ),
            "error": " | ".join(errors[:6]),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "FORUM_DES_IMAGES_ARCHIVE_TYPE",
    "FORUM_DES_IMAGES_COUNTRY",
    "FORUM_DES_IMAGES_INSTITUTION_NAME",
    "FORUM_DES_IMAGES_MAX_BROWSE_PAGES",
    "FORUM_DES_IMAGES_MAX_DETAIL_PAGES",
    "FORUM_DES_IMAGES_PLATFORM_LABEL",
    "FORUM_DES_IMAGES_REPOSITORY_CODE",
    "collect_forum_des_images_dataset",
    "collect_forum_des_images_institutions",
    "parse_forum_des_images_browse_page",
    "parse_forum_des_images_detail_page",
]
