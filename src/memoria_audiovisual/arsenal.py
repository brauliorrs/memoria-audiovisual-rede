import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from .config import (
    ARSENAL_ARCHIVE_DISTRIBUTION_URL,
    ARSENAL_FILM_DATABASE_BROWSE_URL,
    ARSENAL_FILM_DATABASE_URL,
    ARSENAL_HOME_URL,
    HEADERS,
    REQUEST_TIMEOUT,
    ROOT_DIR,
)
from .crawler import normalize_domain, slugify
from .geography import country_to_continent, normalize_country


ARSENAL_REPOSITORY_CODE = "DE-ARSENAL"
ARSENAL_ARCHIVE_TYPE = "Institutional film archive"
ARSENAL_COUNTRY = normalize_country("Germany")
ARSENAL_INSTITUTION_NAME = "Arsenal Filminstitut"
ARSENAL_PLATFORM_LABEL = "Arsenal Film Database"
ARSENAL_PAGE_SIZE = 36
ARSENAL_MAX_WORKERS = 4
ARSENAL_RETRY_ATTEMPTS = 3
ARSENAL_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
)

SESSION = requests.Session()
SESSION.headers.update({**HEADERS, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8,pt-BR;q=0.7"})


def _clean_text(value, *, limit=None):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if limit and len(text) > limit:
        return text[: limit - 1].rstrip() + "..."
    return text


def _as_int(value, default=0):
    try:
        return int(re.sub(r"\D", "", str(value)))
    except (TypeError, ValueError):
        return default


def _playwright_browser_path():
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return
    local_playwright_dir = ROOT_DIR / ".playwright"
    if local_playwright_dir.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local_playwright_dir)


def _fetch(url):
    return SESSION.get(url, timeout=(8, REQUEST_TIMEOUT), allow_redirects=True)


def collect_arsenal_institutions():
    return [
        {
            "institution": ARSENAL_INSTITUTION_NAME,
            "slug": slugify(ARSENAL_INSTITUTION_NAME),
            "country": ARSENAL_COUNTRY,
            "continent": country_to_continent(ARSENAL_COUNTRY),
            "repository_code": ARSENAL_REPOSITORY_CODE,
            "archive_type": ARSENAL_ARCHIVE_TYPE,
            "arsenal_detail_url": ARSENAL_ARCHIVE_DISTRIBUTION_URL,
            "external_url": ARSENAL_FILM_DATABASE_BROWSE_URL,
            "website_available": True,
            "content_available_in_source": True,
        }
    ]


def parse_arsenal_browse_page(html_text, page_url=ARSENAL_FILM_DATABASE_BROWSE_URL):
    soup = BeautifulSoup(html_text or "", "html.parser")
    heading = soup.find("h1")
    total = 0
    if heading:
        match = re.search(r"(\d[\d.,]*)\s+(?:werke|works)\s+(?:gefunden|found)", heading.get_text(" ", strip=True), re.I)
        if match:
            total = _as_int(match.group(1))

    next_link = soup.select_one("a.jscroll-next")
    result_key = ""
    if next_link and next_link.get("href"):
        key_match = re.search(r"/key/([^/]+)", next_link["href"])
        result_key = key_match.group(1) if key_match else ""

    records = []
    for item in soup.select(".bResultItemText"):
        detail_link = item.find("a", href=re.compile(r"/Detail/works/\d+"))
        if not detail_link:
            continue
        detail_url = urljoin(page_url, detail_link["href"])
        record_id = detail_url.rstrip("/").rsplit("/", 1)[-1]
        lines = [_clean_text(line) for line in item.get_text("\n", strip=True).splitlines() if _clean_text(line)]
        title = lines[0] if lines else _clean_text(detail_link.get_text(" ", strip=True))
        metadata = " | ".join(lines[1:])
        year_match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", metadata)
        records.append(
            {
                "record_id": record_id,
                "source_kind": "film_database_index",
                "video_link": detail_url,
                "platform": ARSENAL_PLATFORM_LABEL,
                "title": title,
                "subject": metadata,
                "description": _clean_text(
                    " | ".join(
                        value
                        for value in [
                            "Registro do índice público Browse Works da Arsenal Film Database; ficha audiovisual sem pressupor player aberto ou download de mídia.",
                            metadata,
                        ]
                        if value
                    ),
                    limit=1000,
                ),
                "date": year_match.group(1) if year_match else "",
                "embedded": False,
            }
        )
    return {"total": total, "result_key": result_key, "records": records}


def _new_database_session():
    _playwright_browser_path()
    last_error = ""
    for attempt in range(1, ARSENAL_RETRY_ATTEMPTS + 1):
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    context = browser.new_context(user_agent=ARSENAL_USER_AGENT)
                    page = context.new_page()
                    page.goto(ARSENAL_FILM_DATABASE_BROWSE_URL, wait_until="domcontentloaded", timeout=90000)
                    page.wait_for_timeout(8000)
                    html_text = page.content()
                    if "bResultItemText" not in html_text and "werke gefunden" not in html_text.lower():
                        page.wait_for_timeout(8000)
                        html_text = page.content()
                    if "bResultItemText" not in html_text and "werke gefunden" not in html_text.lower():
                        raise RuntimeError("A Film Database abriu, mas a listagem Browse Works não foi carregada.")
                    cookies = context.cookies()
                finally:
                    browser.close()
                break
        except Exception as error:
            last_error = str(error)
            time.sleep(attempt * 2)
    else:
        raise RuntimeError(last_error or "Falha ao abrir a Film Database por navegador.")

    session = requests.Session()
    session.headers.update({"User-Agent": ARSENAL_USER_AGENT, "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"})
    for cookie in cookies:
        session.cookies.set(
            cookie["name"],
            cookie["value"],
            domain=cookie.get("domain"),
            path=cookie.get("path", "/"),
        )
    return session, html_text


def _browse_page_url(result_key, offset):
    if offset <= 0:
        return ARSENAL_FILM_DATABASE_BROWSE_URL
    return (
        f"{ARSENAL_FILM_DATABASE_BROWSE_URL}/s/{offset}/key/{result_key}"
        "/view/images/sort/Titel/_advanced/0"
    )


def _collect_browse_index():
    session, first_html = _new_database_session()
    first_page = parse_arsenal_browse_page(first_html, ARSENAL_FILM_DATABASE_BROWSE_URL)
    total = first_page["total"]
    result_key = first_page["result_key"]
    pages = [{"offset": 0, "url": ARSENAL_FILM_DATABASE_BROWSE_URL, **first_page}]
    records = list(first_page["records"])
    seen = {record["record_id"] for record in records}

    if not result_key and total > len(records):
        raise RuntimeError("A Film Database respondeu, mas não expôs chave de paginação para completar o índice.")

    cookie_header = "; ".join(f"{cookie.name}={cookie.value}" for cookie in session.cookies)
    headers = {
        "User-Agent": ARSENAL_USER_AGENT,
        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
        "Cookie": cookie_header,
    }

    def fetch_offset(offset):
        url = _browse_page_url(result_key, offset)
        last_error = ""
        for attempt in range(1, ARSENAL_RETRY_ATTEMPTS + 1):
            try:
                response = requests.get(url, headers=headers, timeout=(20, REQUEST_TIMEOUT))
                response.raise_for_status()
                page_data = parse_arsenal_browse_page(response.text, response.url)
                return {"offset": offset, "url": response.url, "error": "", **page_data}
            except Exception as error:
                last_error = str(error)
                time.sleep(attempt)
        return {"offset": offset, "url": url, "total": 0, "result_key": result_key, "records": [], "error": last_error}

    offsets = list(range(ARSENAL_PAGE_SIZE, total, ARSENAL_PAGE_SIZE))
    with ThreadPoolExecutor(max_workers=ARSENAL_MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_offset, offset): offset for offset in offsets}
        for future in as_completed(futures):
            pages.append(future.result())

    page_errors = []
    for page_data in sorted(pages, key=lambda page: page["offset"]):
        if page_data["offset"] == 0:
            continue
        if page_data.get("error"):
            page_errors.append(f"offset {page_data['offset']}: {page_data['error']}")
            continue
        for record in page_data["records"]:
            if record["record_id"] in seen:
                continue
            seen.add(record["record_id"])
            records.append(record)

    return total, records, pages, page_errors


def _base_row(institution):
    return {
        "institution": institution["institution"],
        "slug": institution["slug"],
        "country": institution["country"],
        "continent": institution["continent"],
        "repository_code": ARSENAL_REPOSITORY_CODE,
        "archive_type": ARSENAL_ARCHIVE_TYPE,
        "arsenal_detail_url": ARSENAL_ARCHIVE_DISTRIBUTION_URL,
        "content_available_in_source": True,
        "website_available": True,
    }


def _internal_page_row(institution, url, status, http_code="", video_count=0, embedded_count=0, warning="", error=""):
    return {
        **_base_row(institution),
        "partner_site": ARSENAL_FILM_DATABASE_BROWSE_URL,
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
        "partner_site": ARSENAL_FILM_DATABASE_BROWSE_URL,
        "platform": record.get("platform", ARSENAL_PLATFORM_LABEL),
        "video_link": record.get("video_link", ""),
        "video_title": record.get("title", ""),
        "video_subject": record.get("subject", ""),
        "video_description": record.get("description", ""),
        "video_published_at": record.get("date", ""),
    }


def collect_arsenal_dataset():
    institutions = collect_arsenal_institutions()
    institution = institutions[0]
    internal_pages = []
    records = []
    errors = []
    total_expected = 0

    for url, warning in [
        (ARSENAL_HOME_URL, "Página oficial do Arsenal Filminstitut."),
        (ARSENAL_ARCHIVE_DISTRIBUTION_URL, "Página oficial Archive & Distribution; declara coleção e Film Database."),
        (ARSENAL_FILM_DATABASE_URL, "Rota pública da Film Database; validada via navegador por proteção Anubis."),
    ]:
        try:
            response = _fetch(url)
            response.raise_for_status()
            blocked = "Making sure you&#39;re not a bot" in response.text or "anubis" in response.url.lower()
            internal_pages.append(
                _internal_page_row(
                    institution,
                    response.url,
                    "ok" if not blocked else "bloqueio_navegador_necessario",
                    response.status_code,
                    0,
                    0,
                    warning,
                )
            )
        except Exception as error:
            errors.append(f"{url}: {error}")
            internal_pages.append(_internal_page_row(institution, url, "erro", warning=warning, error=str(error)))

    try:
        total_expected, records, browse_pages, page_errors = _collect_browse_index()
        errors.extend(f"{ARSENAL_FILM_DATABASE_BROWSE_URL}: {error}" for error in page_errors)
        for page_data in browse_pages:
            page_error = page_data.get("error", "")
            internal_pages.append(
                _internal_page_row(
                    institution,
                    page_data["url"],
                    "erro" if page_error else "ok",
                    "" if page_error else 200,
                    len(page_data["records"]),
                    0,
                    f"Página de índice Browse Works offset {page_data['offset']}; total declarado: {total_expected}.",
                    page_error,
                )
            )
    except Exception as error:
        errors.append(f"{ARSENAL_FILM_DATABASE_BROWSE_URL}: {error}")
        internal_pages.append(
            _internal_page_row(
                institution,
                ARSENAL_FILM_DATABASE_BROWSE_URL,
                "erro",
                warning="Falha ao paginar o índice público Browse Works da Film Database.",
                error=str(error),
            )
        )

    video_links = [_record_to_video_row(institution, record) for record in records]
    complete_index = bool(total_expected) and len(video_links) == total_expected and not any(
        error.startswith(ARSENAL_FILM_DATABASE_BROWSE_URL) for error in errors
    )
    summary_warning = (
        "Corpus institucional incorporado pelo índice público Browse Works da Arsenal Film Database. "
        f"A rodada materializou {len(video_links)} de {total_expected or len(video_links)} obras declaradas pela listagem pública. "
        "São fichas descritivas de catálogo; nenhum arquivo de mídia é baixado e a existência de streaming aberto não é presumida. "
        "A rota exige navegador comum por proteção Anubis; a coleta resolve a sessão no Playwright e pagina o índice por HTTP."
    )
    if not complete_index:
        summary_warning = f"{summary_warning} A completude desta rodada deve ser lida como parcial por falha de paginação."

    summary = [
        {
            **_base_row(institution),
            "partner_site": ARSENAL_FILM_DATABASE_BROWSE_URL,
            "partner_domain": normalize_domain(ARSENAL_FILM_DATABASE_BROWSE_URL),
            "status": "ok" if video_links else "erro",
            "http_code": 200 if video_links else "",
            "integrity_status": "integro" if complete_index else "acessivel" if video_links else "instavel",
            "final_url": ARSENAL_FILM_DATABASE_BROWSE_URL,
            "video_links_found_total": len(video_links),
            "embedded_video_signals_total": 0,
            "candidate_internal_pages": len(internal_pages),
            "priority_review": "baixa" if complete_index else "media",
            "warning": summary_warning,
            "error": "; ".join(errors),
        }
    ]
    return institutions, summary, video_links, internal_pages


__all__ = [
    "ARSENAL_MAX_WORKERS",
    "ARSENAL_PAGE_SIZE",
    "ARSENAL_RETRY_ATTEMPTS",
    "collect_arsenal_dataset",
    "collect_arsenal_institutions",
    "parse_arsenal_browse_page",
]
