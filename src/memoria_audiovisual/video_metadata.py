import json
import re

import requests
from bs4 import BeautifulSoup

from .config import HEADERS


SESSION = requests.Session()
SESSION.headers.update(HEADERS)

TITLE_SELECTORS = (
    ("meta", {"property": "og:title"}, "content"),
    ("meta", {"name": "twitter:title"}, "content"),
    ("meta", {"itemprop": "name"}, "content"),
)
DESCRIPTION_SELECTORS = (
    ("meta", {"property": "og:description"}, "content"),
    ("meta", {"name": "description"}, "content"),
    ("meta", {"name": "twitter:description"}, "content"),
)
DATE_SELECTORS = (
    ("meta", {"property": "article:published_time"}, "content"),
    ("meta", {"property": "og:video:release_date"}, "content"),
    ("meta", {"itemprop": "uploadDate"}, "content"),
    ("meta", {"itemprop": "datePublished"}, "content"),
    ("time", {"datetime": True}, "datetime"),
)


def normalize_text(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return text


def clip_text(value, max_length=400):
    text = normalize_text(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + "..."


def extract_tag_value(soup, selectors):
    for tag_name, attrs, attr_name in selectors:
        tag = soup.find(tag_name, attrs=attrs)
        if not tag:
            continue
        value = tag.get(attr_name, "") if attr_name else tag.get_text(" ", strip=True)
        value = normalize_text(value)
        if value:
            return value
    return ""


def extract_json_ld_metadata(soup):
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw_text = script.string or script.get_text(" ", strip=True)
        if not raw_text:
            continue

        try:
            payload = json.loads(raw_text)
        except Exception:
            continue

        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if not isinstance(item, dict):
                continue

            title = normalize_text(item.get("name") or item.get("headline") or "")
            description = normalize_text(item.get("description") or "")
            published_at = normalize_text(
                item.get("uploadDate") or item.get("datePublished") or item.get("dateCreated") or ""
            )
            if title or description or published_at:
                return {
                    "video_title": title,
                    "video_subject": title,
                    "video_description": clip_text(description),
                    "video_published_at": published_at,
                }
    return {}


def extract_title(soup):
    title = extract_tag_value(soup, TITLE_SELECTORS)
    if title:
        return title

    if soup.title:
        return normalize_text(soup.title.get_text(" ", strip=True))
    return ""


def extract_description(soup):
    return clip_text(extract_tag_value(soup, DESCRIPTION_SELECTORS))


def extract_published_at(soup):
    return extract_tag_value(soup, DATE_SELECTORS)


def fetch_video_metadata(url, timeout=20):
    metadata = {
        "video_title": "",
        "video_subject": "",
        "video_description": "",
        "video_published_at": "",
    }
    cleaned_url = normalize_text(url)
    if not cleaned_url:
        return metadata

    try:
        response = SESSION.get(cleaned_url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
    except Exception:
        return metadata

    soup = BeautifulSoup(response.text, "html.parser")

    json_ld = extract_json_ld_metadata(soup)
    if json_ld:
        metadata.update(json_ld)

    if not metadata["video_title"]:
        metadata["video_title"] = extract_title(soup)
    if not metadata["video_subject"]:
        metadata["video_subject"] = metadata["video_title"]
    if not metadata["video_description"]:
        metadata["video_description"] = extract_description(soup)
    if not metadata["video_published_at"]:
        metadata["video_published_at"] = extract_published_at(soup)

    return metadata
