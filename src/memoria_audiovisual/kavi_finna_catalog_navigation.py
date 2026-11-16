"""Pure navigation over the ALREADY approved KAVI metadata-link publication.

The caller MUST validate the publication with load_published_kavi_rows first.
No HTTP, files, media probing, publication, or corpus activation occurs here.
"""
from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

SEARCH_FIELDS = ("video_title", "year", "authors", "genres", "subjects", "languages")
CLASSIFICATIONS = ("film_candidate", "unverified_audiovisual_record")
PAGE_SIZES = (25, 50, 100)


class CatalogNavigationRejected(ValueError):
    """Invalid navigation parameters or untrusted record identity."""


def _fold(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).casefold().strip()


def available_facets(rows: Sequence[Mapping]) -> dict[str, list[str]]:
    """Derive available filters without claiming metadata verification."""
    years: set[str] = set()
    languages: set[str] = set()
    classes: set[str] = set()
    for row in rows:
        year = str(row.get("year", "") or "").strip()
        if year:
            years.add(year)
        for language in str(row.get("languages", "") or "").split(";"):
            language = language.strip()
            if language:
                languages.add(language)
        classification = row.get("film_semantics")
        if classification in CLASSIFICATIONS:
            classes.add(classification)
    return {
        "years": sorted(years, key=lambda x: (_fold(x), x)),
        "languages": sorted(languages, key=lambda x: (_fold(x), x)),
        "classifications": sorted(classes),
    }


def navigate_approved_records(
    rows: Sequence[Mapping], *, query: str = "", year: str = "",
    language: str = "", classification: str = "", page: int = 1,
    page_size: int = 25,
) -> dict:
    """Return a stable, paged selection of validated-publication rows.

    Never call this with staging or preview records. Display links exclusively
    from the approved, separately hash-verified reader.
    """
    if type(page) is not int or page < 1 or type(page_size) is not int or page_size not in PAGE_SIZES:
        raise CatalogNavigationRejected("invalid_pagination")
    if not all(isinstance(x, str) and len(x) <= 200 for x in (query, year, language, classification)):
        raise CatalogNavigationRejected("invalid_filter")
    if classification and classification not in CLASSIFICATIONS:
        raise CatalogNavigationRejected("invalid_classification")
    seen = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise CatalogNavigationRejected("invalid_record")
        rid = row.get("source_record_id")
        link = row.get("video_link")
        if not isinstance(rid, str) or not rid or rid in seen:
            raise CatalogNavigationRejected("duplicate_or_missing_identity")
        # Do not accept ad hoc rows or links from unapproved origins.
        if (row.get("link_status") != "item_link_verified_by_source"
                or row.get("source_record_url") != link
                or not isinstance(link, str) or not link.startswith("https://")
                or row.get("media_access_status") != "unverified"):
            raise CatalogNavigationRejected("unverified_publication_row")
        seen.add(rid)
    term = _fold(query)
    selected = []
    for row in rows:
        if term and not any(term in _fold(row.get(field, "")) for field in SEARCH_FIELDS):
            continue
        if year and _fold(row.get("year", "")) != _fold(year):
            continue
        if language and not any(
            _fold(x) == _fold(language)
            for x in str(row.get("languages", "") or "").split(";")
        ):
            continue
        if classification and row.get("film_semantics") != classification:
            continue
        selected.append(row)
    selected.sort(key=lambda r: (_fold(r.get("video_title", "")), r["source_record_id"]))
    total = len(selected)
    pages = max(1, (total + page_size - 1) // page_size)
    if page > pages:
        raise CatalogNavigationRejected("page_out_of_range")
    start = (page - 1) * page_size
    return {
        "rows": [dict(row) for row in selected[start:start + page_size]],
        "total": total, "page": page, "pages": pages,
        "page_size": page_size,
    }
