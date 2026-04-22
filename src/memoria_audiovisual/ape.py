from io import BytesIO
import re

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .config import APE_CONTENT_PDF_URL, APE_DETAIL_URL_TEMPLATE, HEADERS
from .crawler import clean_url, collect_sites_dataset, slugify
from .geography import COUNTRY_TO_CONTINENT, SPECIAL_COUNTRY_NAMES, country_to_continent, normalize_country


SESSION = requests.Session()
SESSION.headers.update(HEADERS)

APE_PDF_HEADER_PATTERNS = (
    "Status:",
    "This list includes",
    "Country Institution URL for details page",
)
KNOWN_COUNTRY_PREFIXES = {
    normalize_country(name).upper()
    for name in list(COUNTRY_TO_CONTINENT.keys()) + list(SPECIAL_COUNTRY_NAMES.keys())
    if normalize_country(name)
}


def get_soup(url):
    response = SESSION.get(url, timeout=25, allow_redirects=True)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def fetch_pdf_text(url):
    response = SESSION.get(url, timeout=60, allow_redirects=True)
    response.raise_for_status()
    reader = PdfReader(BytesIO(response.content))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def fetch_pdf_reader(url):
    response = SESSION.get(url, timeout=60, allow_redirects=True)
    response.raise_for_status()
    return PdfReader(BytesIO(response.content))


def normalize_pdf_line(line):
    text = str(line or "").replace("\x02", "-")
    text = text.replace("\xad", "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_pdf_noise_line(line):
    normalized = normalize_pdf_line(line)
    if not normalized:
        return True
    if any(normalized.startswith(pattern) for pattern in APE_PDF_HEADER_PATTERNS):
        return True
    if re.fullmatch(r"Page \d+", normalized):
        return True
    return False


def split_country_and_name(prefix, previous_country=""):
    cleaned = normalize_pdf_line(prefix)
    if not cleaned:
        return "", ""

    tokens = cleaned.split()
    best_split = None
    for index in range(1, len(tokens)):
        country_candidate = " ".join(tokens[:index]).upper().strip()
        if country_candidate in KNOWN_COUNTRY_PREFIXES:
            best_split = index

    if best_split is None:
        return normalize_country(previous_country), cleaned

    country_candidate = " ".join(tokens[:best_split]).strip()
    name_candidate = " ".join(tokens[best_split:]).strip()
    return normalize_country(country_candidate), normalize_pdf_line(name_candidate)


def parse_pdf_record(record_lines, previous_country=""):
    joined = " ".join(normalize_pdf_line(line) for line in record_lines if normalize_pdf_line(line))
    if not joined:
        return None, previous_country

    code_match = re.search(r"repositoryCode=([A-Za-z0-9\-]+)", joined)
    if not code_match:
        return None, previous_country

    repository_code = code_match.group(1)
    prefix = joined.split("https://www.archivesportaleurope.net/advanced-search/search-in-institutions/results-", 1)[0]
    country, institution = split_country_and_name(prefix, previous_country=previous_country)
    if not institution:
        return None, previous_country

    record = {
        "institution": institution,
        "slug": slugify(institution),
        "country": country,
        "continent": country_to_continent(country),
        "repository_code": repository_code,
        "ape_detail_url": APE_DETAIL_URL_TEMPLATE.format(repository_code=repository_code),
        "content_available_in_ape": True,
    }
    return record, country or previous_country


def parse_ape_institutions_pdf(url=APE_CONTENT_PDF_URL):
    text = fetch_pdf_text(url)
    lines = text.splitlines()
    records = []
    buffer = []
    previous_country = ""

    for raw_line in lines:
        line = normalize_pdf_line(raw_line)
        if is_pdf_noise_line(line):
            continue

        buffer.append(line)
        if "repositoryCode=" in line:
            record, previous_country = parse_pdf_record(buffer, previous_country=previous_country)
            if record:
                records.append(record)
            buffer = []

    deduplicated = {}
    for record in records:
        deduplicated[record["repository_code"]] = record
    return list(deduplicated.values())


def extract_repository_code_from_url(url):
    match = re.search(r"repositoryCode=([A-Za-z0-9\-]+)", str(url or ""))
    return match.group(1) if match else ""


def parse_ape_institution_links_from_pdf(url=APE_CONTENT_PDF_URL):
    reader = fetch_pdf_reader(url)
    records = {}

    for page in reader.pages:
        annotations = page.get("/Annots", [])
        for annotation_ref in annotations:
            try:
                annotation = annotation_ref.get_object()
            except Exception:
                continue

            action = annotation.get("/A")
            if not action:
                continue

            uri = str(action.get("/URI", "")).strip()
            repository_code = extract_repository_code_from_url(uri)
            if not repository_code:
                continue

            records[repository_code] = {
                "repository_code": repository_code,
                "ape_detail_url": APE_DETAIL_URL_TEMPLATE.format(repository_code=repository_code),
                "content_available_in_ape": True,
            }

    return list(records.values())


def extract_text_between(soup, start_label, stop_labels):
    normalized_start = start_label.strip().lower()
    normalized_stops = {label.strip().lower() for label in stop_labels}
    strings = [
        normalize_pdf_line(text)
        for text in soup.stripped_strings
        if normalize_pdf_line(text)
    ]

    collecting = False
    collected = []
    for text in strings:
        lowered = text.lower()
        if not collecting:
            if lowered == normalized_start:
                collecting = True
            continue

        if lowered in normalized_stops:
            break
        collected.append(text)

    if collected:
        return normalize_pdf_line(" ".join(collected))

    text = soup.get_text("\n", strip=True)
    escaped_stops = "|".join(re.escape(label) for label in stop_labels)
    pattern = rf"{re.escape(start_label)}\s*(.*?)\s*(?:{escaped_stops}|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return normalize_pdf_line(match.group(1))


def extract_table_value(soup, label):
    normalized_label = label.strip().lower().rstrip(":")
    for header in soup.select("td.header, th.header"):
        header_text = normalize_pdf_line(header.get_text(" ", strip=True)).lower().rstrip(":")
        if header_text != normalized_label:
            continue

        value_cell = header.find_next_sibling(["td", "th"])
        if value_cell is None:
            continue

        return normalize_pdf_line(value_cell.get_text(" ", strip=True))
    return ""


def sanitize_ape_country(value):
    cleaned = normalize_pdf_line(value)
    if not cleaned:
        return ""

    noise_markers = [
        "E-mail Address:",
        "Email Address:",
        "Contact this institution",
        "Contact this archive",
        "Last update:",
        "Webpage:",
    ]
    for marker in noise_markers:
        if marker.lower() in cleaned.lower():
            cleaned = re.split(re.escape(marker), cleaned, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    return normalize_country(cleaned)


def sanitize_ape_archive_type(value):
    cleaned = normalize_pdf_line(value)
    if not cleaned:
        return ""

    noise_markers = [
        "Country:",
        "Webpage:",
        "Contact this institution",
        "Contact this archive",
        "Last update:",
    ]
    for marker in noise_markers:
        if marker.lower() in cleaned.lower():
            cleaned = re.split(re.escape(marker), cleaned, maxsplit=1, flags=re.IGNORECASE)[0].strip()

    return cleaned


def extract_ape_website(soup):
    for header in soup.select("td.header, th.header"):
        header_text = normalize_pdf_line(header.get_text(" ", strip=True)).lower().rstrip(":")
        if header_text != "webpage":
            continue

        value_cell = header.find_next_sibling(["td", "th"])
        if value_cell is None:
            continue

        for anchor in value_cell.select("a[href]"):
            href = clean_url(anchor.get("href", ""))
            if not href.startswith("http"):
                continue
            if "archivesportaleurope.net" in href:
                continue
            return href
    return ""


def extract_ape_name(soup):
    heading = soup.select_one("h1")
    if heading:
        return normalize_pdf_line(heading.get_text(" ", strip=True))

    for script in soup.find_all("script"):
        text = script.get_text(" ", strip=True)
        match = re.search(r'document\.title\s*=\s*"([^"]+)"', text)
        if match:
            return normalize_pdf_line(match.group(1))

    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if title:
        return normalize_pdf_line(title.split("|")[0].replace("Results (Institutions)", "").strip())
    return ""


def enrich_ape_institution(record):
    soup = get_soup(record["ape_detail_url"])
    institution_name = extract_ape_name(soup)
    website = extract_ape_website(soup)
    country = sanitize_ape_country(extract_table_value(soup, "Country")) or sanitize_ape_country(
        extract_text_between(
            soup,
            "Country:",
            stop_labels=["Webpage:", "ACCESS & SERVICE INFORMATION", "ARCHIVAL MATERIALS", "Other information"],
        )
    ) or record.get("country", "")
    archive_type = sanitize_ape_archive_type(extract_table_value(soup, "Type of archive")) or sanitize_ape_archive_type(
        extract_text_between(
            soup,
            "Type of archive:",
            stop_labels=["Country:", "Webpage:", "Last update:", "Contact this institution", "Contact this archive"],
        )
    )

    enriched = record.copy()
    enriched["institution"] = institution_name or record.get("institution", "")
    enriched["slug"] = slugify(enriched["institution"]) if enriched["institution"] else record.get("slug", "")
    enriched["country"] = sanitize_ape_country(country or record.get("country", ""))
    enriched["continent"] = country_to_continent(enriched["country"])
    enriched["archive_type"] = archive_type
    enriched["external_url"] = website
    enriched["website_available"] = bool(website)
    return enriched


def collect_ape_institutions():
    institutions = parse_ape_institution_links_from_pdf()
    if not institutions:
        institutions = parse_ape_institutions_pdf()
    enriched = []
    for index, record in enumerate(institutions, start=1):
        label = record.get("institution") or record.get("repository_code", "")
        print(f"[APE details {index}/{len(institutions)}] {label}")
        try:
            enriched.append(enrich_ape_institution(record))
        except Exception:
            fallback = record.copy()
            fallback["institution"] = fallback.get("institution", "")
            fallback["slug"] = slugify(fallback["institution"] or fallback.get("repository_code", "ape-item"))
            fallback["archive_type"] = ""
            fallback["external_url"] = ""
            fallback["website_available"] = False
            fallback["country"] = normalize_country(fallback.get("country", ""))
            fallback["continent"] = country_to_continent(fallback["country"])
            enriched.append(fallback)
    deduplicated = {}
    for record in enriched:
        repository_code = record.get("repository_code", "")
        if repository_code:
            deduplicated[repository_code] = record
    return list(deduplicated.values())


def enrich_rows(rows, entry_lookup):
    enriched_rows = []
    for row in rows:
        extra = entry_lookup.get(row.get("slug"), {})
        merged = row.copy()
        merged["repository_code"] = extra.get("repository_code", "")
        merged["ape_detail_url"] = extra.get("ape_detail_url", "")
        merged["archive_type"] = extra.get("archive_type", "")
        merged["content_available_in_ape"] = extra.get("content_available_in_ape", True)
        merged["website_available"] = extra.get("website_available", False)
        enriched_rows.append(merged)
    return enriched_rows


def collect_ape_dataset():
    institutions = collect_ape_institutions()
    site_entries = []
    for record in institutions:
        site_entries.append(
            {
                "name": record["institution"],
                "slug": record["slug"],
                "country": record.get("country", ""),
                "continent": record.get("continent", ""),
                "external_url": record.get("external_url", ""),
                "detail_url": record.get("ape_detail_url", ""),
            }
        )

    rows_summary, rows_video_links, rows_internal_pages = collect_sites_dataset(site_entries)
    entry_lookup = {
        record["slug"]: {
            "repository_code": record.get("repository_code", ""),
            "ape_detail_url": record.get("ape_detail_url", ""),
            "archive_type": record.get("archive_type", ""),
            "content_available_in_ape": record.get("content_available_in_ape", True),
            "website_available": record.get("website_available", False),
        }
        for record in institutions
    }

    return (
        institutions,
        enrich_rows(rows_summary, entry_lookup),
        enrich_rows(rows_video_links, entry_lookup),
        enrich_rows(rows_internal_pages, entry_lookup),
    )
