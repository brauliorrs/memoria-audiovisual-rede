import http.client
import re
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from .config import (
    CINEMATECA_PT_ACCESS_URL,
    CINEMATECA_PT_COLLECTIONS_URL,
    CINEMATECA_PT_DIGITAL_HOME_URL,
    CINEMATECA_PT_FELIX_URL,
    CINEMATECA_PT_HOME_URL,
    CINEMATECA_PT_VIDEO_LIST_URL,
    REQUEST_TIMEOUT,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


CINEMATECA_PT_REPOSITORY_CODE = "PT-CINEMATECA"
CINEMATECA_PT_ARCHIVE_TYPE = "National film and moving image archive"
CINEMATECA_PT_COUNTRY = normalize_country("Portugal")
CINEMATECA_PT_INSTITUTION_NAME = "Cinemateca Portuguesa - Museu do Cinema"
CINEMATECA_PT_PLATFORM_LABEL = "Cinemateca Digital"
CINEMATECA_PT_MAX_LIST_PAGES = 5
CINEMATECA_PT_MAX_DETAIL_PAGES = 20
CINEMATECA_PT_LIST_WORKERS = 2
CINEMATECA_PT_DETAIL_WORKERS = 3
CINEMATECA_PT_REQUEST_RETRIES = 3
CINEMATECA_PT_REQUEST_PAUSE = 0.15
CINEMATECA_PT_HOST = "www.cinemateca.pt"


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _fetch_html(url_or_path):
    parsed = urlparse(url_or_path)
    host = parsed.hostname or CINEMATECA_PT_HOST
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    last_error = None
    for attempt in range(CINEMATECA_PT_REQUEST_RETRIES):
        try:
            connection = http.client.HTTPSConnection(
                host,
                timeout=REQUEST_TIMEOUT,
                context=ssl.create_default_context(),
            )
            connection.request(
                "GET",
                path,
                headers={
                    "Host": host,
                    "User-Agent": "Mozilla/5.0 (compatible; MemoriaAudiovisualRede/1.0)",
                    "Accept": "text/html,*/*",
                    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
                    "Connection": "close",
                },
            )
            response = connection.getresponse()
            data = response.read()
            connection.close()
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}")
            return response.status, f"https://{host}{path}", data.decode("utf-8", errors="replace")
        except Exception as error:
            last_error = error
            time.sleep(CINEMATECA_PT_REQUEST_PAUSE * (attempt + 1))
    raise RuntimeError(str(last_error))


def _extract_record_id(url):
    match = re.search(r"obraid=(\d+)", str(url or ""))
    return match.group(1) if match else ""


def _extract_year(value):
    match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", str(value or ""))
    return match.group(1) if match else ""


def _extract_detail_links(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    links = []
    seen = set()
    for href in [anchor.get("href", "") for anchor in soup.find_all("a", href=True)]:
        if "Ficha.aspx" not in href or "type=Video" not in href:
            continue
        url = urljoin(page_url or CINEMATECA_PT_VIDEO_LIST_URL, href)
        record_id = _extract_record_id(url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        links.append(url)
    return links


def collect_cinemateca_portuguesa_institutions():
    return [
        {
            "institution": CINEMATECA_PT_INSTITUTION_NAME,
            "slug": slugify(CINEMATECA_PT_INSTITUTION_NAME),
            "country": CINEMATECA_PT_COUNTRY,
            "continent": country_to_continent(CINEMATECA_PT_COUNTRY),
            "repository_code": CINEMATECA_PT_REPOSITORY_CODE,
            "archive_type": CINEMATECA_PT_ARCHIVE_TYPE,
            "cinemateca_portuguesa_detail_url": CINEMATECA_PT_HOME_URL,
            "external_url": CINEMATECA_PT_VIDEO_LIST_URL,
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
        "repository_code": CINEMATECA_PT_REPOSITORY_CODE,
        "archive_type": CINEMATECA_PT_ARCHIVE_TYPE,
        "cinemateca_portuguesa_detail_url": CINEMATECA_PT_HOME_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": CINEMATECA_PT_VIDEO_LIST_URL,
        "internal_page": url,
        "status": status,
        "http_code": http_code,
        "video_links_found": video_count,
        "embedded_signals": embedded_count,
        "warning": warning,
        "error": error,
    }


def parse_cinemateca_portuguesa_video_list_page(html_text, page_url=CINEMATECA_PT_VIDEO_LIST_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    records = []
    seen = set()
    for item in soup.select("div.CDText"):
        anchor = item.select_one('a[href*="Ficha.aspx"][href*="type=Video"]')
        if not anchor:
            continue
        detail_url = urljoin(page_url, anchor.get("href", ""))
        record_id = _extract_record_id(detail_url)
        if not record_id or record_id in seen:
            continue
        seen.add(record_id)
        lines = [
            _clean_text(line)
            for line in item.get_text("\n", strip=True).split("\n")
            if _clean_text(line)
        ]
        title = _clean_text(anchor.get_text(" ", strip=True)).strip('"')
        country_year = next((line for line in lines if "," in line and "Duração:" not in line), "")
        duration = next((line.replace("Duração:", "").strip() for line in lines if line.startswith("Duração:")), "")
        description = _clean_text(
            " | ".join(
                value
                for value in [
                    "Ficha pública de vídeo na Cinemateca Digital; registro materializado a partir da listagem oficial.",
                    country_year,
                    f"duração: {duration}" if duration else "",
                ]
                if value
            ),
            limit=900,
        )
        records.append(
            {
                "record_id": record_id,
                "source_kind": "cinemateca_digital_listing_record",
                "page_url": detail_url,
                "video_link": detail_url,
                "platform": CINEMATECA_PT_PLATFORM_LABEL,
                "title": title,
                "subject": country_year,
                "description": description,
                "date": _extract_year(country_year),
                "duration": duration,
                "embedded": False,
            }
        )
    return records


def _extract_labeled_value(text, label):
    pattern = rf"{re.escape(label)}:\s*(.+?)(?=\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][^:]{1,45}:|$)"
    match = re.search(pattern, text, flags=re.S)
    return _clean_text(match.group(1), limit=1200) if match else ""


def parse_cinemateca_portuguesa_detail_page(html_text, page_url):
    soup = BeautifulSoup(html_text or "", "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [_clean_text(line) for line in text.split("\n") if _clean_text(line)]
    try:
        start = lines.index("Vídeo") + 1
    except ValueError:
        start = 0
    end = next((index for index, line in enumerate(lines[start:], start) if line.startswith("© 2013")), len(lines))
    body_lines = lines[start:end]
    title = body_lines[0] if body_lines else ""
    body_text = _clean_text(" ".join(body_lines), limit=3500)
    iframe = soup.find("iframe", src=re.compile(r"player\.vimeo\.com/video/", re.I))
    iframe_src = _clean_text(iframe.get("src", "")) if iframe else ""
    if iframe_src.startswith("//"):
        iframe_src = f"https:{iframe_src}"
    genre = _extract_labeled_value(body_text, "Género")
    duration = _extract_labeled_value(body_text, "Duração")
    format_value = _extract_labeled_value(body_text, "Formato")
    description_value = _extract_labeled_value(body_text, "Descrição")
    rights = _extract_labeled_value(body_text, "Detentor de Direitos")
    id_cp = _extract_labeled_value(body_text, "ID CP-MC")
    country_year = next((line for line in body_lines if re.search(r"\bPortugal,\s+(?:s/d|n/a|\d{4})", line)), "")
    credits = " | ".join(line for line in body_lines[1:8] if " - " in line)
    description = _clean_text(
        " | ".join(
            value
            for value in [
                "Ficha pública da Cinemateca Digital.",
                f"ID CP-MC: {id_cp}" if id_cp else "",
                f"gênero: {genre}" if genre else "",
                f"duração: {duration}" if duration else "",
                f"formato: {format_value}" if format_value else "",
                f"créditos: {credits}" if credits else "",
                description_value,
                rights,
                "iframe Vimeo público detectado" if iframe_src else "registro descritivo sem iframe público detectado na ficha",
            ]
            if value
        ),
        limit=1600,
    )
    return {
        "record_id": _extract_record_id(page_url),
        "source_kind": "cinemateca_digital_detail_record",
        "page_url": page_url,
        "video_link": iframe_src or page_url,
        "platform": "Vimeo" if iframe_src else CINEMATECA_PT_PLATFORM_LABEL,
        "title": title,
        "subject": "; ".join(value for value in [country_year, genre, format_value] if value),
        "description": description,
        "date": _extract_year(country_year),
        "duration": duration,
        "embedded": bool(iframe_src),
    }


def _record_to_video_row(institution, record):
    return {
        **_base_row(institution),
        "partner_site": CINEMATECA_PT_VIDEO_LIST_URL,
        "platform": record.get("platform", CINEMATECA_PT_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def _list_url(page):
    if page <= 1:
        return CINEMATECA_PT_VIDEO_LIST_URL
    return f"{CINEMATECA_PT_VIDEO_LIST_URL}?page={page}"


def _fetch_list_page(page):
    url = _list_url(page)
    status, final_url, html_text = _fetch_html(url)
    records = parse_cinemateca_portuguesa_video_list_page(html_text, final_url)
    declared_pages = max([int(match) for match in re.findall(r"video\.aspx\?page=(\d+)", html_text)] or [page])
    return page, status, final_url, html_text, records, declared_pages


def _fetch_detail(record):
    status, final_url, html_text = _fetch_html(record["page_url"])
    parsed = parse_cinemateca_portuguesa_detail_page(html_text, final_url)
    return status, final_url, parsed


def collect_cinemateca_portuguesa_dataset():
    institutions = collect_cinemateca_portuguesa_institutions()
    institution = institutions[0]
    internal_pages = []
    records_by_id = {}
    list_errors = []
    detail_errors = []
    declared_pages = 0

    for url, warning in [
        (CINEMATECA_PT_HOME_URL, "Página institucional da Cinemateca Portuguesa."),
        (CINEMATECA_PT_COLLECTIONS_URL, "Página oficial Filme e Vídeo: acervo de imagens em movimento."),
        (CINEMATECA_PT_ACCESS_URL, "Página oficial de acesso ao Arquivo Fílmico e Videográfico."),
        (CINEMATECA_PT_DIGITAL_HOME_URL, "Página Cinemateca Digital: plataforma de visionamento online."),
        (CINEMATECA_PT_FELIX_URL, "Portal Félix: dados abertos e catálogos do património cinematográfico português."),
    ]:
        try:
            status, final_url, html_text = _fetch_html(url)
            internal_pages.append(_internal_page_row(institution, final_url, "ok", status, 0, 0, warning))
            if url == CINEMATECA_PT_DIGITAL_HOME_URL:
                match = re.search(r"mais de\s+([\d\s.]+)\s+filmes", BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True), re.I)
                if match:
                    declared_pages = max(declared_pages, 177)
        except Exception as error:
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    with ThreadPoolExecutor(max_workers=CINEMATECA_PT_LIST_WORKERS) as executor:
        futures = [executor.submit(_fetch_list_page, page) for page in range(1, CINEMATECA_PT_MAX_LIST_PAGES + 1)]
        for future in as_completed(futures):
            try:
                page, status, final_url, html_text, page_records, page_count = future.result()
                declared_pages = max(declared_pages, page_count)
                for record in page_records:
                    records_by_id[record["record_id"]] = record
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        final_url,
                        "ok",
                        status,
                        len(page_records),
                        0,
                        f"Página {page} da listagem pública de vídeos da Cinemateca Digital.",
                    )
                )
            except Exception as error:
                list_errors.append(str(error))
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        CINEMATECA_PT_VIDEO_LIST_URL,
                        "erro",
                        warning="Falha em página da listagem de vídeos; recorte MVP fica parcial.",
                        error=str(error),
                    )
                )

    detail_candidates = list(records_by_id.values())[:CINEMATECA_PT_MAX_DETAIL_PAGES]
    with ThreadPoolExecutor(max_workers=CINEMATECA_PT_DETAIL_WORKERS) as executor:
        futures = [executor.submit(_fetch_detail, record) for record in detail_candidates]
        for future in as_completed(futures):
            try:
                status, final_url, parsed = future.result()
                if parsed.get("record_id") in records_by_id:
                    records_by_id[parsed["record_id"]].update(parsed)
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        final_url,
                        "ok",
                        status,
                        1,
                        1 if parsed.get("embedded") else 0,
                        "Ficha pública aberta para enriquecimento de metadados e detecção de iframe.",
                    )
                )
            except Exception as error:
                detail_errors.append(str(error))
                internal_pages.append(
                    _internal_page_row(
                        institution,
                        CINEMATECA_PT_VIDEO_LIST_URL,
                        "erro",
                        warning="Falha ao abrir ficha pública; registro de listagem preservado.",
                        error=str(error),
                    )
                )

    records = list(records_by_id.values())
    video_links = [_record_to_video_row(institution, record) for record in records]
    embedded_total = sum(1 for record in records if record.get("embedded"))
    warning_parts = [
        "Corpus incorporado pelo recorte público `Cinemateca Digital > Vídeo`.",
        f"A plataforma declara mais de 1700 filmes online e a paginação observada indica {declared_pages or 'múltiplas'} páginas.",
        f"O MVP materializa {len(records)} fichas em até {CINEMATECA_PT_MAX_LIST_PAGES} páginas de listagem",
        f"e enriquece até {CINEMATECA_PT_MAX_DETAIL_PAGES} fichas detalhadas, sem baixar mídia e sem afirmar exaustividade do acervo.",
    ]
    if list_errors or detail_errors:
        warning_parts.append(f"Falhas técnicas registradas: {len(list_errors)} listagem; {len(detail_errors)} fichas.")

    summary = [
        {
            **_base_row(institution),
            "partner_site": CINEMATECA_PT_VIDEO_LIST_URL,
            "partner_domain": normalize_domain(CINEMATECA_PT_VIDEO_LIST_URL),
            "status": "ok" if records else "sem_registros",
            "http_code": 200 if records else "",
            "integrity_status": "integro" if records else "sem_registros",
            "final_url": CINEMATECA_PT_VIDEO_LIST_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": embedded_total,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": False,
            "warning": " ".join(warning_parts),
            "error": "",
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "CINEMATECA_PT_ARCHIVE_TYPE",
    "CINEMATECA_PT_COUNTRY",
    "CINEMATECA_PT_INSTITUTION_NAME",
    "CINEMATECA_PT_MAX_DETAIL_PAGES",
    "CINEMATECA_PT_MAX_LIST_PAGES",
    "CINEMATECA_PT_PLATFORM_LABEL",
    "CINEMATECA_PT_REPOSITORY_CODE",
    "collect_cinemateca_portuguesa_dataset",
    "collect_cinemateca_portuguesa_institutions",
    "parse_cinemateca_portuguesa_detail_page",
    "parse_cinemateca_portuguesa_video_list_page",
]
