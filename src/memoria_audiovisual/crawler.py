import re
import time
from urllib.parse import quote, urljoin, urlparse

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

        external_url = None
        node = heading.find_next()
        steps = 0

        while node and steps < 40:
            if getattr(node, "name", None) == "a":
                href = node.get("href", "").strip()
                if href.startswith("http") and "iasa-web.org" not in href:
                    external_url = href
                    break

            if getattr(node, "name", None) == "h2":
                break

            node = node.find_next()
            steps += 1

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
        return response
    except PlaywrightTimeoutError:
        return None
    except Exception:
        return None


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
        links.add(urljoin(base_url, href))
    return links


def detect_embeds(page, base_url):
    detected = []
    selectors = ["iframe[src]", "video[src]", "audio[src]", "source[src]"]

    for selector in selectors:
        try:
            srcs = page.eval_on_selector_all(
                selector,
                "els => els.map(e => e.getAttribute('src')).filter(Boolean)",
            )
        except Exception:
            continue

        for src in srcs:
            detected.append(urljoin(base_url, src))

    return list(dict.fromkeys(detected))


def detect_json_video_hints(page):
    try:
        html = page.content()
    except Exception:
        return []

    patterns = [
        r'https?://[^\s"\']+youtube\.com[^\s"\']*',
        r'https?://[^\s"\']+youtu\.be[^\s"\']*',
        r'https?://[^\s"\']+vimeo\.com[^\s"\']*',
        r'https?://[^\s"\']+archive\.org[^\s"\']*',
        r'https?://[^\s"\']+dailymotion\.com[^\s"\']*',
        r'https?://[^\s"\']+\.(?:mp4|m3u8|webm|mp3|wav|m4v)',
    ]

    hints = []
    for pattern in patterns:
        hints.extend(re.findall(pattern, html, flags=re.IGNORECASE))
    return list(dict.fromkeys(hints))


def analyze_page_with_playwright(page, url):
    result = {
        "status": "erro",
        "http_code": "",
        "final_url": url,
        "video_platform_links": [],
        "embedded_video_links": [],
        "embedded_video_signals": 0,
        "candidate_internal_pages": [],
        "error": "",
    }

    response = safe_goto(page, url)
    final_url = page.url

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
        if platform:
            platform_links.append((platform, full_url))
        if is_internal_to_site(final_url, full_url) and looks_like_video_url(full_url):
            candidate_internal_pages.append(full_url)

    for full_url in result["embedded_video_links"]:
        platform = classify_platform(full_url)
        if platform:
            platform_links.append((platform, full_url))

    result["video_platform_links"] = list(dict.fromkeys(platform_links))
    result["candidate_internal_pages"] = list(dict.fromkeys(candidate_internal_pages))[:MAX_INTERNAL_PAGES]
    return result


def compute_priority(status, video_links_found_total, embedded_total):
    if status in {"erro", "restrito", "http_error"}:
        return "alta"
    if video_links_found_total > 0 or embedded_total > 0:
        return "media"
    return "baixa"


def classify_integrity(status, http_code):
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
                "partner_site": external_url,
                "internal_page": subpage["final_url"],
                "status": subpage["status"],
                "http_code": subpage["http_code"],
                "video_links_found": len(subpage["video_platform_links"]),
                "embedded_signals": subpage["embedded_video_signals"],
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
        "integrity_status": classify_integrity(home["status"], home["http_code"]),
        "final_url": home["final_url"],
        "video_links_found_total": len(all_video_links),
        "embedded_video_signals_total": embedded_total,
        "candidate_internal_pages": len(home["candidate_internal_pages"]),
        "priority_review": compute_priority(home["status"], len(all_video_links), embedded_total),
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
        page = browser.new_page()

        for index, entry in enumerate(entries, start=1):
            name = entry["name"]
            slug = entry["slug"]
            external_url = entry["external_url"]
            print(f"[{index}/{len(entries)}] {name} -> {external_url}")

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
                    "error": str(error),
                }
                video_rows = []
                internal_rows = []

            rows_summary.append(summary)
            rows_video_links.extend(video_rows)
            rows_internal_pages.extend(internal_rows)
            time.sleep(SLEEP_BETWEEN_REQUESTS)

        browser.close()

    return entries, rows_summary, rows_video_links, rows_internal_pages
