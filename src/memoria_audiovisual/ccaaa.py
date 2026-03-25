from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import CCAAA_MEMBERS_URL, HEADERS, IASA_CCAAA_URL
from .crawler import collect_sites_dataset, slugify


SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def get_soup(url):
    response = SESSION.get(url, timeout=25, allow_redirects=True)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def normalize_url(url):
    value = str(url or "").strip()
    if not value:
        return ""
    if value.startswith("//"):
        return "https:" + value
    if value.startswith("www."):
        return "https://" + value
    return value


def normalize_domain(url):
    try:
        domain = urlparse(normalize_url(url)).netloc.lower().strip()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def extract_abbreviation(name):
    text = str(name or "").strip()
    if "(" in text and ")" in text:
        inside = text.split("(")[-1].split(")")[0].strip()
        if inside and inside.upper() == inside:
            return inside
    if " (" in text:
        return text.split(" (")[-1].rstrip(")")
    return ""


def extract_external_link_from_block(start_node):
    node = start_node.find_next_sibling()
    steps = 0

    while node and steps < 12:
        if getattr(node, "name", None) == "h4":
            break
        for anchor in getattr(node, "select", lambda *_args, **_kwargs: [])("a[href]"):
            href = normalize_url(anchor.get("href", ""))
            if href.startswith("http") and "ccaaa.org" not in normalize_domain(href):
                return href
        node = node.find_next_sibling()
        steps += 1
    return ""


def extract_description_from_block(start_node):
    node = start_node.find_next_sibling()
    parts = []
    steps = 0

    while node and steps < 12:
        if getattr(node, "name", None) == "h4":
            break
        text = getattr(node, "get_text", lambda *args, **kwargs: "")(" ", strip=True)
        if text and not text.startswith("www."):
            parts.append(text)
        node = node.find_next_sibling()
        steps += 1

    return " ".join(parts).strip()


def parse_ccaaa_members_page():
    soup = get_soup(CCAAA_MEMBERS_URL)
    rows = []
    seen = set()

    for heading in soup.select("h4"):
        name = heading.get_text(" ", strip=True)
        if not name:
            continue

        website = extract_external_link_from_block(heading)
        if not website:
            continue

        domain = normalize_domain(website)
        key = (name, domain)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "organization": name,
                "abbreviation": extract_abbreviation(name),
                "role": "member",
                "website": website,
                "domain": domain,
                "description": extract_description_from_block(heading),
                "source": "ccaaa_members_page",
            }
        )

    return rows


def parse_iasa_ccaaa_page():
    soup = get_soup(IASA_CCAAA_URL)
    rows = []
    seen = set()

    marker = soup.find(string=lambda text: text and "Current membership is limited to nine organisations" in text)
    if not marker:
        return rows

    list_node = marker.find_parent().find_next("ul")
    if not list_node:
        return rows

    for item in list_node.select("li"):
        text = item.get_text(" ", strip=True)
        anchor = item.select_one("a[href]")
        website = normalize_url(anchor.get("href", "")) if anchor else ""
        name = text
        role = "member"

        if "observer status" in text.lower():
            role = "observer"
            name = text.split("has observer status")[0].strip()

        if website:
            domain = normalize_domain(website)
        else:
            domain = ""

        key = (name, domain, role)
        if key in seen:
            continue
        seen.add(key)

        rows.append(
            {
                "organization": name,
                "abbreviation": extract_abbreviation(name),
                "role": role,
                "website": website,
                "domain": domain,
                "description": "",
                "source": "iasa_ccaaa_page",
            }
        )

    return rows


def merge_member_rows(*sources):
    merged = {}

    for rows in sources:
        for row in rows:
            domain = row.get("domain") or normalize_domain(row.get("website", ""))
            key = domain or row.get("organization", "").lower()
            existing = merged.get(key, {}).copy()

            for field in ["organization", "abbreviation", "role", "website", "domain", "description"]:
                if row.get(field):
                    existing[field] = row[field]
                elif field not in existing:
                    existing[field] = ""

            existing_sources = set(filter(None, str(existing.get("source", "")).split("|")))
            existing_sources.add(row.get("source", ""))
            existing["source"] = "|".join(sorted(filter(None, existing_sources)))
            merged[key] = existing

    result = list(merged.values())
    result.sort(key=lambda row: (row.get("role") != "member", row.get("organization", "")))
    return result


def collect_ccaaa_members():
    iasa_rows = parse_iasa_ccaaa_page()
    ccaaa_rows = parse_ccaaa_members_page()
    return merge_member_rows(iasa_rows, ccaaa_rows)


def build_ccaaa_site_entries(ccaaa_members):
    entries = []

    for row in ccaaa_members:
        website = normalize_url(row.get("website", ""))
        if not website:
            continue

        entries.append(
            {
                "name": row["organization"],
                "slug": slugify(row["organization"]),
                "external_url": website,
                "country": "",
                "continent": "",
                "abbreviation": row.get("abbreviation", ""),
                "role": row.get("role", ""),
                "member_source": row.get("source", ""),
            }
        )

    return entries


def enrich_ccaaa_rows(rows, entry_lookup):
    enriched = []
    for row in rows:
        extra = entry_lookup.get(row.get("slug"), {})
        merged = row.copy()
        merged["abbreviation"] = extra.get("abbreviation", "")
        merged["role"] = extra.get("role", "")
        merged["member_source"] = extra.get("member_source", "")
        enriched.append(merged)
    return enriched


def collect_ccaaa_dataset(ccaaa_members=None):
    members = ccaaa_members or collect_ccaaa_members()
    entries = build_ccaaa_site_entries(members)
    rows_summary, rows_video_links, rows_internal_pages = collect_sites_dataset(entries)
    entry_lookup = {
        entry["slug"]: {
            "abbreviation": entry.get("abbreviation", ""),
            "role": entry.get("role", ""),
            "member_source": entry.get("member_source", ""),
        }
        for entry in entries
    }

    return (
        entries,
        enrich_ccaaa_rows(rows_summary, entry_lookup),
        enrich_ccaaa_rows(rows_video_links, entry_lookup),
        enrich_ccaaa_rows(rows_internal_pages, entry_lookup),
    )
