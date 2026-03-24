import re
import time
from html import unescape
from urllib.parse import parse_qs, quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .config import (
    BASE_URL,
    HEADERS,
    MAX_INTERNAL_PAGES,
    PLAYWRIGHT_TIMEOUT,
    REQUEST_TIMEOUT,
    SLEEP_BETWEEN_REQUESTS,
    START_URL,
    VIDEO_FILE_EXTENSIONS,
    VIDEO_HINTS_IN_URL,
    VIDEO_PLATFORMS,
)


SESSION = requests.Session()
SESSION.headers.update(HEADERS)

STOP_SECTION_TITLES = {"pages"}
SKIP_URL_SCHEMES = ("mailto:", "tel:", "javascript:", "#")
GENERIC_URL_TOKENS = (
    "privacy",
    "policy",
    "policies",
    "cookie",
    "cookies",
    "terms",
    "about",
    "help",
    "faq",
    "support",
    "signup",
    "register",
    "login",
    "logout",
    "sharer",
    "share.php",
    "player.js",
)
EMBED_HINTS = ("/embed/", "/player/", "/video/", "/videos/", "/watch/", "/reel/")
GENERIC_FINAL_URL_TOKENS = (
    "cgi-sys/suspendedpage.cgi",
    "cgi-sys/defaultwebpage.cgi",
    "/fehler-404",
    "/404",
)
GENERIC_PAGE_TITLE_TOKENS = (
    "404",
    "not found",
    "suspended",
    "default webpage",
    "coming soon",
    "under construction",
)


def get_soup(url):
    response = SESSION.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser"), response


def normalize_domain(url):
    try:
        netloc = urlparse(url).netloc.lower().strip()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def clean_url(raw_url):
    if not raw_url:
        return ""
    cleaned = unescape(raw_url).strip()
    cleaned = cleaned.replace("\\u0026", "&").replace("\\u003d", "=").replace("\\/", "/")
    cleaned = cleaned.rstrip("\\")
    cleaned = cleaned.strip(' "\'<>')
    if not cleaned:
        return ""

    protocol_matches = list(re.finditer(r"https?://", cleaned, flags=re.IGNORECASE))
    if len(protocol_matches) > 1:
        cleaned = cleaned[: protocol_matches[1].start()]

    lowered = cleaned.lower()
    if lowered.startswith(SKIP_URL_SCHEMES):
        return ""
    return cleaned


def classify_platform(url):
    domain = normalize_domain(url)
    for known, label in VIDEO_PLATFORMS.items():
        if domain == known or domain.endswith("." + known):
            return label
    return None


def is_internal_to_site(base_url, target_url):
    return normalize_domain(base_url) == normalize_domain(target_url)


def looks_like_video_url(url):
    lowered = url.lower()
    if any(ext in lowered for ext in VIDEO_FILE_EXTENSIONS):
        return True
    if any(hint in lowered for hint in VIDEO_HINTS_IN_URL):
        return True
    return classify_platform(url) is not None


def is_generic_platform_url(url):
    lowered = url.lower()
    return any(token in lowered for token in GENERIC_URL_TOKENS)


def is_probably_video_link(url, platform=None):
    cleaned = clean_url(url)
    if not cleaned:
        return False

    lowered = cleaned.lower()
    parsed = urlparse(cleaned)
    path = parsed.path.lower()
    query = parse_qs(parsed.query)
    platform = platform or classify_platform(cleaned)

    if any(ext in lowered for ext in VIDEO_FILE_EXTENSIONS):
        return True
    if is_generic_platform_url(cleaned):
        return False

    if platform == "YouTube":
        path_parts = [part for part in path.split("/") if part]
        return (
            (parsed.netloc.lower().endswith("youtu.be") and bool(path_parts))
            or ("watch" in path and bool(query.get("v")))
            or (path.startswith("/shorts/") and len(path_parts) >= 2)
            or (path.startswith("/embed/") and len(path_parts) >= 2)
            or (path.startswith("/live/") and len(path_parts) >= 2)
        )

    if platform == "Vimeo":
        path_parts = [part for part in path.split("/") if part]
        return (
            parsed.netloc.lower().startswith("player.vimeo.com")
            and path.startswith("/video/")
            and len(path_parts) >= 2
        ) or bool(re.fullmatch(r"/\d+", path))

    if platform == "Facebook":
        return (
            "/videos/" in path
            or path.startswith("/watch") and "v" in query
            or path.startswith("/reel/")
            or "/share/v/" in path
        )

    if platform == "Instagram":
        return path.startswith("/reel/") or path.startswith("/p/") or path.startswith("/tv/")

    if platform == "Dailymotion":
        return "/video/" in path

    if platform == "Internet Archive":
        return "/details/" in path or "/embed/" in path

    if platform == "SoundCloud":
        return False

    return any(hint in path for hint in EMBED_HINTS)


def sanitize_final_url(requested_url, candidate_url):
    cleaned_candidate = clean_url(candidate_url)
    if not cleaned_candidate:
        return requested_url
    lowered = cleaned_candidate.lower()
    if lowered.startswith("chrome-error://") or lowered == "about:blank":
        return requested_url
    return cleaned_candidate


def detect_page_warning(final_url, page_title):
    lowered_url = (final_url or "").lower()
    lowered_title = (page_title or "").lower()

    if any(token in lowered_url for token in GENERIC_FINAL_URL_TOKENS):
        return "Pagina generica, suspensa ou de erro apesar de responder."
    if any(token in lowered_title for token in GENERIC_PAGE_TITLE_TOKENS):
        return "Titulo da pagina sugere erro ou landing page generica."
    return ""


def extract_entry_block(heading):
    nodes = []
    node = heading.next_sibling
    while node:
        if getattr(node, "name", None) == "h2":
            break
        nodes.append(node)
        node = node.next_sibling
    return nodes


def block_text(nodes):
    parts = []
    for node in nodes:
        text = getattr(node, "get_text", lambda *args, **kwargs: str(node))(" ", strip=True)
        if text:
            parts.append(text)
    return " ".join(parts)


def extract_external_url_from_block(nodes):
    for node in nodes:
        if getattr(node, "name", None) == "a":
            href = clean_url(node.get("href", ""))
            if href.startswith("http") and "iasa-web.org" not in href:
                return href

        for anchor in getattr(node, "select", lambda *args, **kwargs: [])("a[href]"):
            href = clean_url(anchor.get("href", ""))
            if href.startswith("http") and "iasa-web.org" not in href:
                return href
    return None


def find_next_iasa_page(soup):
    for anchor in soup.select("a[href]"):
        text = anchor.get_text(" ", strip=True).lower()
        href = anchor.get("href", "").strip()
        if "next" in text and href:
            return urljoin(BASE_URL, href)
    return None


def extract_entry_links_from_iasa_page(soup):
    entries = []
    seen = set()

    for heading in soup.select("h2"):
        name = heading.get_text(" ", strip=True)
        if not name:
            continue
        if name.lower() in STOP_SECTION_TITLES:
            break

        nodes = extract_entry_block(heading)
        text = block_text(nodes).lower()
        if "url:" not in text or "country:" not in text:
            continue

        external_url = extract_external_url_from_block(nodes)

        if external_url:
            key = (name, external_url)
            if key not in seen:
                seen.add(key)
                entries.append(
                    {
                        "name": name,
                        "slug": slugify(name),
                        "external_url": external_url,
                    }
                )

    return entries


def crawl_iasa_category():
    all_entries = []
    visited = set()
    url = START_URL

    while url and url not in visited:
        print(f"[IASA] Lendo: {url}")
        visited.add(url)
        soup, _response = get_soup(url)
        all_entries.extend(extract_entry_links_from_iasa_page(soup))
        url = find_next_iasa_page(soup)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    deduplicated = {}
    for entry in all_entries:
        deduplicated[(entry["name"], entry["external_url"])] = entry
    return list(deduplicated.values())


def safe_goto(page, url):
    try:
        response = page.goto(url, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
        page.wait_for_timeout(1500)
        final_url = sanitize_final_url(url, page.url)
        return response, final_url
    except PlaywrightTimeoutError:
        return None, url
    except Exception:
        return None, url


def extract_links_from_dom(page, base_url):
    links = set()
    try:
        hrefs = page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => e.getAttribute('href')).filter(Boolean)",
        )
    except Exception:
        return links

    for href in hrefs:
        cleaned = clean_url(href)
        if cleaned:
            links.add(urljoin(base_url, cleaned))
    return links


def detect_embeds(page, base_url):
    detected = []
    selector_rules = {
        "iframe[src]": False,
        "video[src]": True,
        "audio[src]": True,
        "source[src]": True,
    }

    for selector, allow_media_tag in selector_rules.items():
        try:
            srcs = page.eval_on_selector_all(
                selector,
                "els => els.map(e => e.getAttribute('src')).filter(Boolean)",
            )
        except Exception:
            continue

        for src in srcs:
            cleaned = clean_url(src)
            if not cleaned:
                continue
            full_url = urljoin(base_url, cleaned)
            platform = classify_platform(full_url)
            if allow_media_tag or is_probably_video_link(full_url, platform):
                detected.append(full_url)

    return list(dict.fromkeys(detected))


def detect_json_video_hints(page):
    try:
        html = page.content()
    except Exception:
        return []

    patterns = [r'https?://[^\s"\'<>]+']

    hints = []
    for pattern in patterns:
        hints.extend(re.findall(pattern, html, flags=re.IGNORECASE))
    filtered = []
    for hint in hints:
        cleaned = clean_url(hint)
        if not cleaned:
            continue
        platform = classify_platform(cleaned)
        if is_probably_video_link(cleaned, platform):
            filtered.append(cleaned)
    return list(dict.fromkeys(filtered))


def analyze_page_with_playwright(page, url):
    result = {
        "status": "erro",
        "http_code": "",
        "final_url": url,
        "page_title": "",
        "warning": "",
        "video_platform_links": [],
        "embedded_video_links": [],
        "embedded_video_signals": 0,
        "candidate_internal_pages": [],
        "error": "",
    }

    response, final_url = safe_goto(page, url)

    if response is None:
        result["final_url"] = final_url
        result["error"] = "Timeout ou falha no carregamento"
        return result

    try:
        status_code = response.status
    except Exception:
        status_code = ""

    result["http_code"] = status_code
    result["final_url"] = final_url
    try:
        result["page_title"] = page.title()
    except Exception:
        result["page_title"] = ""
    result["warning"] = detect_page_warning(final_url, result["page_title"])

    if status_code in (401, 403):
        result["status"] = "restrito"
    elif isinstance(status_code, int) and status_code >= 400:
        result["status"] = "http_error"
    else:
        result["status"] = "ok"

    all_links = extract_links_from_dom(page, final_url)
    embedded_links = detect_embeds(page, final_url)
    html_hints = detect_json_video_hints(page)
    result["embedded_video_links"] = list(dict.fromkeys(embedded_links + html_hints))
    result["embedded_video_signals"] = len(result["embedded_video_links"])

    platform_links = []
    candidate_internal_pages = []
    for full_url in all_links:
        platform = classify_platform(full_url)
        if platform and is_probably_video_link(full_url, platform):
            platform_links.append((platform, full_url))
        if is_internal_to_site(final_url, full_url) and looks_like_video_url(full_url):
            candidate_internal_pages.append(full_url)

    for full_url in result["embedded_video_links"]:
        platform = classify_platform(full_url)
        if platform and is_probably_video_link(full_url, platform):
            platform_links.append((platform, full_url))

    result["video_platform_links"] = list(dict.fromkeys(platform_links))
    result["candidate_internal_pages"] = list(dict.fromkeys(candidate_internal_pages))[:MAX_INTERNAL_PAGES]
    return result


def compute_priority(status, video_links_found_total, embedded_total, warning=""):
    if warning:
        return "alta"
    if status in {"erro", "restrito", "http_error"}:
        return "alta"
    if video_links_found_total > 0 or embedded_total > 0:
        return "media"
    return "baixa"


def classify_integrity(status, http_code):
    return classify_integrity_with_warning(status, http_code, "")


def classify_integrity_with_warning(status, http_code, warning):
    if status == "ok" and warning:
        return "suspeito"
    if status == "ok" and http_code == 200:
        return "integro"
    if status == "ok":
        return "acessivel"
    if status == "restrito":
        return "restrito"
    if status == "http_error":
        return "quebrado"
    return "instavel"


def slugify(value):
    lowered = value.lower().strip()
    normalized = re.sub(r"[^a-z0-9]+", "-", lowered)
    return normalized.strip("-") or quote(value.strip())


def analyze_institution(page, institution_name, external_url):
    home = analyze_page_with_playwright(page, external_url)
    internal_results = []
    all_video_links = list(home["video_platform_links"])
    embedded_total = home["embedded_video_signals"]

    for internal_url in home["candidate_internal_pages"][:MAX_INTERNAL_PAGES]:
        subpage = analyze_page_with_playwright(page, internal_url)
        internal_results.append(
            {
                "institution": institution_name,
                "slug": slugify(institution_name),
                "partner_site": external_url,
                "internal_page": subpage["final_url"],
                "status": subpage["status"],
                "http_code": subpage["http_code"],
                "video_links_found": len(subpage["video_platform_links"]),
                "embedded_signals": subpage["embedded_video_signals"],
                "warning": subpage["warning"],
                "error": subpage["error"],
            }
        )
        all_video_links.extend(subpage["video_platform_links"])
        embedded_total += subpage["embedded_video_signals"]
        time.sleep(0.4)

    all_video_links = list(dict.fromkeys(all_video_links))

    summary = {
        "institution": institution_name,
        "slug": slugify(institution_name),
        "partner_site": external_url,
        "partner_domain": normalize_domain(home["final_url"] or external_url),
        "status": home["status"],
        "http_code": home["http_code"],
        "integrity_status": classify_integrity_with_warning(
            home["status"], home["http_code"], home["warning"]
        ),
        "final_url": home["final_url"],
        "video_links_found_total": len(all_video_links),
        "embedded_video_signals_total": embedded_total,
        "candidate_internal_pages": len(home["candidate_internal_pages"]),
        "priority_review": compute_priority(
            home["status"], len(all_video_links), embedded_total, home["warning"]
        ),
        "warning": home["warning"],
        "error": home["error"],
    }

    video_rows = [
        {
            "institution": institution_name,
            "slug": slugify(institution_name),
            "partner_site": external_url,
            "platform": platform,
            "video_link": link,
        }
        for platform, link in all_video_links
    ]

    return summary, video_rows, internal_results


def collect_dataset():
    entries = crawl_iasa_category()
    rows_summary = []
    rows_video_links = []
    rows_internal_pages = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)

        for index, entry in enumerate(entries, start=1):
            name = entry["name"]
            slug = entry["slug"]
            external_url = entry["external_url"]
            print(f"[{index}/{len(entries)}] {name} -> {external_url}")
            page = browser.new_page()

            try:
                summary, video_rows, internal_rows = analyze_institution(page, name, external_url)
            except Exception as error:
                summary = {
                    "institution": name,
                    "slug": slug,
                    "partner_site": external_url,
                    "partner_domain": normalize_domain(external_url),
                    "status": "erro",
                    "http_code": "",
                    "integrity_status": "instavel",
                    "final_url": external_url,
                    "video_links_found_total": 0,
                    "embedded_video_signals_total": 0,
                    "candidate_internal_pages": 0,
                    "priority_review": "alta",
                    "warning": "",
                    "error": str(error),
                }
                video_rows = []
                internal_rows = []
            finally:
                page.close()

            rows_summary.append(summary)
            rows_video_links.extend(video_rows)
            rows_internal_pages.extend(internal_rows)
            time.sleep(SLEEP_BETWEEN_REQUESTS)

    return entries, rows_summary, rows_video_links, rows_internal_pages
