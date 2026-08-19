"""Tipagem determinística e conservadora de superfícies públicas do MAR.

A classificação serve à inteligência/automação do observatório. Ela não transforma
uma página em evidência científica e não substitui revisão humana. Em caso de
ambiguidade, a decisão deve permanecer ``unknown``.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal, Mapping, Sequence
from urllib.parse import parse_qs, urlsplit

SurfaceType = Literal[
    "homepage",
    "institutional_landing_page",
    "archive_landing_page",
    "search_or_index",
    "news_or_editorial",
    "item_record",
    "audiovisual_item",
    "restricted_or_unavailable",
    "unknown",
]

SurfaceConfidence = Literal["low", "medium", "high"]

SURFACE_TYPES: tuple[SurfaceType, ...] = (
    "homepage",
    "institutional_landing_page",
    "archive_landing_page",
    "search_or_index",
    "news_or_editorial",
    "item_record",
    "audiovisual_item",
    "restricted_or_unavailable",
    "unknown",
)

ITEM_LEVEL_SURFACE_TYPES = {"item_record", "audiovisual_item"}

_SEARCH_TOKENS = {
    "search",
    "recherche",
    "buscar",
    "busca",
    "results",
    "resultats",
    "resultados",
}
_NEWS_TOKENS = {
    "news",
    "actualite",
    "actualites",
    "article",
    "articles",
    "blog",
    "press",
    "presse",
    "magazine",
    "story",
    "stories",
}
_ARCHIVE_TOKENS = {
    "archive",
    "archives",
    "arquivo",
    "acervo",
    "archivo",
    "collection",
    "collections",
    "colecao",
    "coleccion",
    "catalog",
    "catalogue",
    "catalogo",
    "fonds",
}
_ITEM_TOKENS = {
    "item",
    "record",
    "notice",
    "detail",
    "details",
    "work",
    "asset",
    "media",
    "film",
    "video",
    "audio",
}
_UNAVAILABLE_STATUSES = {
    "blocked_by_robots",
    "request_error",
    "http_error",
}

_ID_LIKE_RE = re.compile(r"(?=.*\d)[a-z0-9][a-z0-9._~-]{5,}$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SurfaceTypeDecision:
    surface_type: SurfaceType
    confidence: SurfaceConfidence
    evidence: tuple[str, ...]

    @property
    def is_item_level(self) -> bool:
        return self.surface_type in ITEM_LEVEL_SURFACE_TYPES

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["is_item_level"] = self.is_item_level
        return data


def _normalize(value: str | None) -> str:
    return (value or "").casefold().strip()


def _path_tokens(url: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in re.split(r"[^a-z0-9]+", urlsplit(url).path.casefold())
        if token
    )


def _canonical_identity(url: str) -> tuple[str, str, str]:
    parts = urlsplit(url)
    host = (parts.hostname or "").casefold().removeprefix("www.")
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return parts.scheme.casefold(), host, path


def _contains_any(text: str, terms: set[str]) -> tuple[str, ...]:
    found = [term for term in sorted(terms) if term in text]
    return tuple(found)


def _confidence(score: int, *, high_at: int = 6) -> SurfaceConfidence:
    if score >= high_at:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


def classify_surface_type(
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
    """Classifica uma superfície sem converter sinais fracos em certeza.

    A prioridade é evitar falsos positivos em nível de item. ``item_record`` exige
    combinação de sinais de item; ``audiovisual_item`` exige, adicionalmente,
    evidência pública de mídia ou marcação audiovisual estruturada.
    """

    normalized_status = _normalize(fetch_status)
    if normalized_status in _UNAVAILABLE_STATUSES:
        return SurfaceTypeDecision(
            "restricted_or_unavailable",
            "high",
            (f"fetch_status:{normalized_status}",),
        )

    parts = urlsplit(url)
    tokens = _path_tokens(url)
    token_set = set(tokens)
    title_norm = _normalize(title)
    text_norm = _normalize(text)
    metadata_norm = _normalize(metadata_text)
    structured_norm = _normalize(structured_text)
    combined_meta = "\n".join((title_norm, metadata_norm, structured_norm))
    root_identity = _canonical_identity(root_url)
    page_identity = _canonical_identity(url)
    is_root_surface = page_identity == root_identity

    query = {key.casefold() for key in parse_qs(parts.query, keep_blank_values=True)}

    search_evidence: list[str] = []
    search_score = 0
    search_path = sorted(token_set & _SEARCH_TOKENS)
    if search_path:
        search_score += 3
        search_evidence.append(f"path:{search_path[0]}")
    if query & {"q", "query", "search", "keyword", "keywords", "term"}:
        search_score += 2
        search_evidence.append("query:search-parameter")
    search_title = _contains_any(title_norm, _SEARCH_TOKENS)
    if search_title:
        search_score += 2
        search_evidence.append(f"title:{search_title[0]}")
    if search_score >= 4:
        return SurfaceTypeDecision(
            "search_or_index",
            _confidence(search_score),
            tuple(search_evidence),
        )

    news_evidence: list[str] = []
    news_score = 0
    news_path = sorted(token_set & _NEWS_TOKENS)
    if news_path:
        news_score += 3
        news_evidence.append(f"path:{news_path[0]}")
    if "newsarticle" in structured_norm or '"@type":"article"' in structured_norm.replace(" ", ""):
        news_score += 4
        news_evidence.append("structured:article")
    news_title = _contains_any(title_norm, _NEWS_TOKENS)
    if news_title:
        news_score += 2
        news_evidence.append(f"title:{news_title[0]}")
    if news_score >= 4:
        return SurfaceTypeDecision(
            "news_or_editorial",
            _confidence(news_score),
            tuple(news_evidence),
        )

    item_evidence: list[str] = []
    item_score = 0
    item_path = sorted(token_set & _ITEM_TOKENS)
    if item_path:
        item_score += 2
        item_evidence.append(f"path:{item_path[0]}")
    tail = tokens[-1] if tokens else ""
    if tail and tail not in _ITEM_TOKENS and tail not in _ARCHIVE_TOKENS and _ID_LIKE_RE.fullmatch(tail):
        item_score += 2
        item_evidence.append("path:id-like-tail")
    if title_norm and len(title_norm) >= 3:
        item_score += 1
        item_evidence.append("title:present")
    if any(marker in structured_norm for marker in ("videoobject", "audioobject", '"@type":"movie"', '"@type": "movie"')):
        item_score += 4
        item_evidence.append("structured:audiovisual-object")
    if "identifier" in structured_norm or "identifier" in metadata_norm:
        item_score += 1
        item_evidence.append("metadata:identifier")

    media_evidence: list[str] = []
    media_score = 0
    if media_urls:
        media_score += 2
        media_evidence.append("media:embedded-or-linked")
    if any(marker in structured_norm for marker in ("videoobject", "audioobject", "contenturl", "embedurl")):
        media_score += 3
        media_evidence.append("structured:media")
    if any(marker in metadata_norm for marker in ("og:video", "og:audio", "twitter:player")):
        media_score += 2
        media_evidence.append("metadata:media")

    if item_score >= 4 and media_score >= 2:
        return SurfaceTypeDecision(
            "audiovisual_item",
            _confidence(item_score + media_score, high_at=7),
            tuple(item_evidence + media_evidence),
        )
    if item_score >= 4:
        return SurfaceTypeDecision(
            "item_record",
            _confidence(item_score),
            tuple(item_evidence),
        )

    archive_evidence: list[str] = []
    archive_score = 0
    archive_path = sorted(token_set & _ARCHIVE_TOKENS)
    if archive_path:
        archive_score += 2
        archive_evidence.append(f"path:{archive_path[0]}")
        if len(token_set & _ARCHIVE_TOKENS) > 1 or sum(token in _ARCHIVE_TOKENS for token in tokens) > 1:
            archive_score += 1
            archive_evidence.append("path:repeated-archive-context")
    archive_title = _contains_any(title_norm, _ARCHIVE_TOKENS)
    if archive_title:
        archive_score += 2
        archive_evidence.append(f"title:{archive_title[0]}")
    if any(phrase in text_norm for phrase in ("browse the collection", "explore the collection", "consulter les archives", "explorer les archives", "consultar o acervo")):
        archive_score += 1
        archive_evidence.append("text:archive-navigation")
    if archive_score >= 4:
        return SurfaceTypeDecision(
            "archive_landing_page",
            _confidence(archive_score),
            tuple(archive_evidence),
        )

    if is_root_surface and (parts.path in {"", "/"}):
        return SurfaceTypeDecision("homepage", "high", ("root_surface:/",))

    if is_root_surface:
        return SurfaceTypeDecision(
            "institutional_landing_page",
            "medium",
            ("root_surface:non-home-path",),
        )

    if any(marker in combined_meta for marker in ("about us", "about the", "qui sommes-nous", "a propos", "sobre nos", "sobre nós")):
        return SurfaceTypeDecision(
            "institutional_landing_page",
            "low",
            ("metadata:institutional-context",),
        )

    return SurfaceTypeDecision("unknown", "low", ())


def classify_surface_mapping(
    page: Mapping[str, object],
    *,
    root_url: str,
) -> SurfaceTypeDecision:
    media_urls = page.get("media_urls")
    if not isinstance(media_urls, (list, tuple)):
        media_urls = ()
    return classify_surface_type(
        url=str(page.get("url") or ""),
        root_url=root_url,
        title=str(page.get("title")) if page.get("title") is not None else None,
        text=str(page.get("text") or ""),
        metadata_text=str(page.get("metadata_text") or ""),
        structured_text=str(page.get("structured_text") or ""),
        media_urls=tuple(str(value) for value in media_urls),
        fetch_status=str(page.get("fetch_status") or "fetched"),
    )


__all__ = [
    "ITEM_LEVEL_SURFACE_TYPES",
    "SURFACE_TYPES",
    "SurfaceConfidence",
    "SurfaceType",
    "SurfaceTypeDecision",
    "classify_surface_mapping",
    "classify_surface_type",
]
