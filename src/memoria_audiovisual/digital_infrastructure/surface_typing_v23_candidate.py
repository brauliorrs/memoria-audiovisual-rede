"""Post-VAL-007 development candidate for MAR M3 surface typing.

This module deliberately leaves the frozen 2.2.0 classifier unchanged. VAL-007 is
now development evidence only for the next protocol generation; no result produced
here may be reported as independent validation. A future 2.3.0 release still
requires a new preregistered, prediction-frozen ecological validation on unseen
corpora.

The candidate addresses generic architecture failures observed after VAL-007:

* configured observation roots are not automatically semantic homepages;
* audiovisual detail routes may use singular/plural ``film/video/audio/clip``
  path families and trailing slashes;
* fiche/detail pages may express audiovisual type in query values rather than keys;
* direct public media can confirm an otherwise generic audiovisual detail route;
* filtered archive/index surfaces may use author/creator/category query keys;
* multilingual collection/archive browse markers are recognized without encoding
  institution names, IDs or exact slugs.
"""

from __future__ import annotations

import re
from typing import Sequence
from urllib.parse import parse_qs, unquote, urlsplit

from memoria_audiovisual.digital_infrastructure.surface_typing import (
    SurfaceTypeDecision,
    classify_surface_type as classify_surface_type_v22,
)

SURFACE_TYPING_CANDIDATE_VERSION = "2.3.0-dev"

_AV_ROUTE_SEGMENTS = {
    "video",
    "videos",
    "film",
    "films",
    "movie",
    "movies",
    "audio",
    "audios",
    "clip",
    "clips",
}
_AV_QUERY_VALUES = {
    "video",
    "videos",
    "film",
    "films",
    "movie",
    "movies",
    "audio",
    "audios",
    "clip",
    "clips",
}
_DETAIL_MARKERS = {
    "fiche",
    "ficha",
    "scheda",
    "detail",
    "details",
    "record",
    "item",
    "notice",
}
_INDEX_QUERY_KEYS = {
    "author",
    "authors",
    "creator",
    "creators",
    "category",
    "categories",
    "genre",
    "genres",
    "tag",
    "tags",
}
_INDEX_ROOT_STEMS = {
    "archive",
    "archives",
    "archivio",
    "arhiv",
    "catalog",
    "catalogue",
    "catalogo",
    "browse",
    "watch",
    "ogladaj",
    "video",
    "videos",
    "film",
    "films",
    "movie",
    "movies",
    "audio",
    "audios",
    "clip",
    "clips",
}
_COLLECTION_ROUTE_TOKENS = {
    "colecoes",
    "colecao",
    "coleções",
    "coleção",
    "collezioni",
    "collezione",
    "colecciones",
    "coleccion",
    "collection",
    "collections",
}
_GENERIC_DETAIL_SEGMENTS = {
    "about",
    "index",
    "search",
    "browse",
    "archive",
    "archives",
    "catalog",
    "catalogue",
    "category",
    "categories",
}


def _normalize(value: str | None) -> str:
    return (value or "").casefold().strip()


def _path_segments(url: str) -> tuple[str, ...]:
    path = unquote(urlsplit(url).path).casefold().rstrip("/")
    return tuple(segment for segment in path.split("/") if segment)


def _segment_stem(segment: str) -> str:
    return segment.rsplit(".", 1)[0]


def _path_tokens(url: str) -> set[str]:
    path = unquote(urlsplit(url).path).casefold()
    return {token for token in re.split(r"[^a-z0-9à-ÿ]+", path) if token}


def _query_parts(url: str) -> tuple[set[str], set[str]]:
    parsed = parse_qs(urlsplit(url).query, keep_blank_values=True)
    keys = {key.casefold() for key in parsed}
    values: set[str] = set()
    for items in parsed.values():
        for value in items:
            values.update(
                token
                for token in re.split(r"[^a-z0-9à-ÿ]+", unquote(value).casefold())
                if token
            )
    return keys, values


def _has_direct_media(
    *,
    metadata_text: str,
    structured_text: str,
    media_urls: Sequence[str],
) -> bool:
    if media_urls:
        return True
    metadata = _normalize(metadata_text)
    structured = _normalize(structured_text)
    return any(
        marker in metadata
        for marker in ("og:video", "og:audio", "twitter:player", "video_frames")
    ) or any(
        marker in structured
        for marker in ("videoobject", "audioobject", "contenturl", "embedurl")
    )


def _detail_segment_looks_specific(segment: str) -> bool:
    stem = _segment_stem(segment)
    if stem in _GENERIC_DETAIL_SEGMENTS:
        return False
    if re.search(r"\d{4,}", stem):
        return True
    if re.search(r"[a-zà-ÿ]+[-_][a-zà-ÿ]+", stem):
        return len(stem) >= 10
    return False


def _explicit_av_detail(url: str) -> tuple[bool, str | None]:
    segments = _path_segments(url)
    for index, segment in enumerate(segments[:-1]):
        stem = _segment_stem(segment)
        if stem not in _AV_ROUTE_SEGMENTS:
            continue
        detail = segments[index + 1]
        if _segment_stem(detail) in _GENERIC_DETAIL_SEGMENTS:
            continue
        return True, detail
    return False, None


def _looks_like_alpha_index(title: str) -> bool:
    normalized = _normalize(title)
    return bool(
        re.search(r"\b[a-z]\s*[-–—]\s*[a-z]\b", normalized)
        or re.search(r"[а-я]\s*[-–—]\s*[а-я]", normalized)
    )


def _root_stem(url: str) -> str:
    segments = _path_segments(url)
    return _segment_stem(segments[-1]) if segments else ""


def classify_surface_type_candidate(
    *,
    url: str,
    root_url: str,
    title: str | None = None,
    text: str = "",
    metadata_text: str = "",
    structured_text: str = "",
    media_urls: Sequence[str] = (),
    fetch_status: str = "fetched",
) -> SurfaceTypeDecision:
    """Return a 2.3.0-development decision layered over frozen protocol 2.2.0."""

    base = classify_surface_type_v22(
        url=url,
        root_url=root_url,
        title=title,
        text=text,
        metadata_text=metadata_text,
        structured_text=structured_text,
        media_urls=media_urls,
        fetch_status=fetch_status,
    )

    title_norm = _normalize(title)
    tokens = _path_tokens(url)
    query_keys, query_values = _query_parts(url)
    direct_media = _has_direct_media(
        metadata_text=metadata_text,
        structured_text=structured_text,
        media_urls=media_urls,
    )
    explicit_av_detail, detail_segment = _explicit_av_detail(url)
    query_declares_av = bool(query_values & _AV_QUERY_VALUES)
    fiche_or_detail = bool(tokens & _DETAIL_MARKERS)
    has_facet_query = any(
        key in {"filter", "filters", "facet", "facets"}
        or key.startswith("f[")
        or key.startswith("filter[")
        or key.startswith("facet[")
        for key in query_keys
    )

    # Preserve explicit filter/facet semantics before attempting an item upgrade.
    if not has_facet_query:
        if fiche_or_detail and (query_declares_av or direct_media):
            return SurfaceTypeDecision(
                "audiovisual_item",
                "high" if direct_media else "medium",
                tuple(base.evidence)
                + (
                    "candidate:path-fiche-or-detail",
                    "candidate:query-av-type" if query_declares_av else "candidate:direct-media",
                ),
                base.access_state,
                base.access_evidence,
            )

        if explicit_av_detail and detail_segment is not None and (
            direct_media or _detail_segment_looks_specific(detail_segment)
        ):
            return SurfaceTypeDecision(
                "audiovisual_item",
                "high" if direct_media else "medium",
                tuple(base.evidence)
                + (
                    "candidate:path-explicit-av-detail",
                    "candidate:direct-media"
                    if direct_media
                    else "candidate:detail-specificity",
                ),
                base.access_state,
                base.access_evidence,
            )

    # Query filters that choose author/creator/category describe an index, not an item.
    if query_keys & _INDEX_QUERY_KEYS and base.surface_type not in {
        "audiovisual_item",
        "item_record",
    }:
        return SurfaceTypeDecision(
            "search_or_index",
            "medium",
            tuple(base.evidence) + ("candidate:query-index-filter",),
            base.access_state,
            base.access_evidence,
        )

    # An observation root is a crawler configuration, not semantic homepage evidence.
    # Reclassify only when generic browse/index signals are present; true site roots
    # and unrelated configured entry pages retain the 2.2.0 decision.
    if base.surface_type == "homepage" and (urlsplit(url).path or "/") not in {"", "/"}:
        stem = _root_stem(url)
        plural_av_title = any(
            marker in title_norm
            for marker in (
                "films",
                "videos",
                "movies",
                "clips",
                "filmes",
                "vídeos",
                "vidéos",
            )
        )
        archive_alpha_index = _looks_like_alpha_index(title_norm) and any(
            marker in title_norm
            for marker in ("archive", "archives", "archivio", "arhiv", "архив")
        )
        if stem in _INDEX_ROOT_STEMS or plural_av_title or archive_alpha_index:
            return SurfaceTypeDecision(
                "search_or_index",
                "medium",
                tuple(base.evidence) + ("candidate:semantic-index-root",),
                base.access_state,
                base.access_evidence,
            )

    # Multilingual collection routes without item evidence are archive landing pages.
    # Only upgrade unresolved 2.2.0 surfaces; do not overwrite an existing semantic
    # institutional landing decision from an earlier frozen development fixture.
    if base.surface_type == "unknown" and (tokens & _COLLECTION_ROUTE_TOKENS):
        return SurfaceTypeDecision(
            "archive_landing_page",
            "medium",
            tuple(base.evidence) + ("candidate:path-collection-landing",),
            base.access_state,
            base.access_evidence,
        )

    return base


__all__ = [
    "SURFACE_TYPING_CANDIDATE_VERSION",
    "classify_surface_type_candidate",
]
