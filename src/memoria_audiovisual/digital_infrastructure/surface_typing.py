"""Tipagem determinística e conservadora de superfícies públicas do MAR.

A classificação serve à inteligência/automação do observatório. Ela não transforma
uma página em evidência científica e não substitui revisão humana. Em caso de
ambiguidade, a decisão deve permanecer ``unknown``.

Desde o protocolo 2.0.0, o papel semântico da superfície e o estado de acesso/coleta
são dimensões independentes. Um bloqueio do coletor, redirecionamento ou restrição
geográfica não deve, por si só, redefinir o tipo da superfície observada.

O protocolo 2.2.0 responde à validação ecológica independente do 2.1.0 sem
introduzir regras específicas por instituição: páginas de listagem podem ser
reconhecidas por sinais estruturais e textuais fortes, e rotas singulares de
audiovisual com marcador explícito de conteúdo (por exemplo, trailer/episódio)
podem confirmar item audiovisual mesmo quando o coletor não extrai uma URL de
mídia reproduzível. Conflitos humanos estruturalmente indistinguíveis permanecem
como limitação de desenvolvimento e não são codificados por ID ou slug.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Literal, Mapping, Sequence
from urllib.parse import parse_qs, unquote, urlsplit

SURFACE_TYPING_PROTOCOL_VERSION = "2.2.0"

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
SurfaceAccessState = Literal[
    "accessible",
    "geo_restricted",
    "collector_blocked",
    "redirect_outside_scope",
    "request_error",
    "http_error",
    "unknown",
]

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
    "browse",
    "index",
    "results",
    "resultats",
    "resultados",
    "consulta",
    "consultar",
    "consulter",
    "zoek",
    "zoeken",
    "zoekresultaten",
}
_EDITORIAL_PATH_TOKENS = {
    "about",
    "news",
    "actualite",
    "actualites",
    "article",
    "articles",
    "blog",
    "magazine",
    "story",
    "stories",
}
_EDITORIAL_WEAK_TOKENS = {"press", "presse"}
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
_CATALOGUE_TOKENS = {"catalog", "catalogue", "catalogo"}
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
    "films",
    "video",
    "videos",
    "audio",
    "audios",
    "movie",
    "movies",
}
_AUDIOVISUAL_PATH_TOKENS = {
    "film",
    "films",
    "video",
    "videos",
    "audio",
    "audios",
    "movie",
    "movies",
}
_AUDIOVISUAL_PLURAL_PATH_TOKENS = {"films", "videos", "audios", "movies"}
_RECORDISH_PATH_TOKENS = {
    "item",
    "record",
    "notice",
    "detail",
    "details",
    "work",
    "asset",
    "media",
}
_AJAX_INDEX_TOKENS = {
    "kwtheme",
    "kwname",
    "keyword",
    "keywords",
    "filter",
    "facet",
    "theme",
    "format",
    "mots",
    "cles",
}
_SEARCH_TEXT_MARKERS = (
    "advanced search",
    "recherche avanc",
    "pesquisa avanç",
    "busqueda avanzada",
    "búsqueda avanzada",
    "appliquer la recherche",
    "filter results",
    "filter by",
    "filtrer",
    "filtern",
    "plus de résultats",
    "more results",
    "show more results",
    "seitennummerierung",
)
_AUDIOVISUAL_TITLE_MARKERS = (
    "trailer",
    "teaser",
    "episode",
    "épisode",
    "episodio",
    "episódio",
    "video clip",
    "vidéo clip",
)
_RESTRICTED_ROUTE_FRAGMENTS = (
    "/acces-pro",
    "/espace-perso",
    "/login",
    "/signin",
    "/sign-in",
    "/account",
    "/mon-compte",
    "/restricted",
    "/private",
)

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5]?[0-9a-f]{3}-[89ab]?[0-9a-f]{3}-[0-9a-f]{12}",
    re.IGNORECASE,
)
_LONG_ID_RE = re.compile(r"(?=.*\d)[a-z0-9][a-z0-9._~-]{5,}$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SurfaceTypeDecision:
    surface_type: SurfaceType
    confidence: SurfaceConfidence
    evidence: tuple[str, ...]
    access_state: SurfaceAccessState = "accessible"
    access_evidence: tuple[str, ...] = ()

    @property
    def is_item_level(self) -> bool:
        return self.surface_type in ITEM_LEVEL_SURFACE_TYPES

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["is_item_level"] = self.is_item_level
        data["protocol_version"] = SURFACE_TYPING_PROTOCOL_VERSION
        return data


def _normalize(value: str | None) -> str:
    return (value or "").casefold().strip()


def _path_tokens(url: str) -> tuple[str, ...]:
    path = unquote(urlsplit(url).path).casefold()
    return tuple(token for token in re.split(r"[^a-z0-9]+", path) if token)


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


def _same_host_and_under_root(url: str, root_url: str) -> bool:
    page = urlsplit(url)
    root = urlsplit(root_url)
    page_host = (page.hostname or "").casefold().removeprefix("www.")
    root_host = (root.hostname or "").casefold().removeprefix("www.")
    if not page_host or page_host != root_host:
        return False
    root_path = (root.path or "/").rstrip("/") or "/"
    page_path = (page.path or "/").rstrip("/") or "/"
    if root_path == "/":
        return True
    return page_path == root_path or page_path.startswith(f"{root_path}/")


def _access_state(
    *,
    fetch_status: str,
    title: str,
    text: str,
    metadata_text: str,
) -> tuple[SurfaceAccessState, tuple[str, ...]]:
    status = _normalize(fetch_status)
    combined = "\n".join((title, text, metadata_text))

    geo_markers = (
        "geo restricted",
        "geo-restricted",
        "geographically restricted",
        "playback denied: location",
        "player_err_geo_restricted",
        "unavailable from your current location",
    )
    if any(marker in combined for marker in geo_markers):
        return "geo_restricted", ("content:geo-restriction",)
    if status == "blocked_by_robots":
        return "collector_blocked", ("fetch_status:blocked_by_robots",)
    if status == "redirect_outside_scope":
        return "redirect_outside_scope", ("fetch_status:redirect_outside_scope",)
    if status == "request_error":
        return "request_error", ("fetch_status:request_error",)
    if status == "http_error":
        return "http_error", ("fetch_status:http_error",)
    if status in {"", "fetched", "completed"}:
        return "accessible", ()
    return "unknown", (f"fetch_status:{status}",) if status else ()


def _item_specificity(url: str, tokens: tuple[str, ...], query_keys: set[str]) -> tuple[int, list[str]]:
    score = 0
    evidence: list[str] = []
    path = unquote(urlsplit(url).path).casefold()
    basename = path.rsplit("/", 1)[-1]
    stem = basename.rsplit(".", 1)[0]

    if _UUID_RE.search(path):
        score += 3
        evidence.append("path:uuid")

    numeric_groups = re.findall(r"\d{2,}", stem)
    if len(numeric_groups) >= 2:
        score += 2
        evidence.append("path:multiple-numeric-id-groups")
    elif any(len(group) >= 5 for group in numeric_groups):
        score += 2
        evidence.append("path:long-numeric-id")

    tail = tokens[-1] if tokens else ""
    if tail and tail not in _ITEM_TOKENS and tail not in _ARCHIVE_TOKENS and _LONG_ID_RE.fullmatch(tail):
        score += 2
        evidence.append("path:id-like-tail")

    if query_keys & {"id", "item", "record", "asset", "video", "media"}:
        score += 2
        evidence.append("query:item-identifier")

    return score, evidence


def _has_facet_query(query_keys: set[str]) -> bool:
    return any(
        key in {"filter", "filters", "facet", "facets"}
        or key.startswith("f[")
        or key.startswith("filter[")
        or key.startswith("facet[")
        for key in query_keys
    )


def _looks_restricted_route(path: str, token_set: set[str]) -> bool:
    path_norm = unquote(path).casefold()
    if any(fragment in path_norm for fragment in _RESTRICTED_ROUTE_FRAGMENTS):
        return True
    return {"acces", "pro"}.issubset(token_set) or {"espace", "perso"}.issubset(token_set)


def _has_explicit_audiovisual_detail_route(path: str) -> bool:
    """Detecta uma rota singular de AV seguida por um segmento de detalhe.

    A regra é estrutural e independente de domínio. `/video` ou `/videos`
    sozinhos não bastam; é necessário um segmento posterior não vazio.
    """
    segments = [
        segment
        for segment in unquote(path).casefold().split("/")
        if segment
    ]
    singular = {"video", "audio", "film", "movie"}
    for index, segment in enumerate(segments[:-1]):
        if segment in singular and segments[index + 1]:
            return True
    return False


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
    """Classifica o papel semântico da superfície e registra acesso separadamente.

    A precedência é deliberada: superfícies de restrição e consulta/filtro são
    resolvidas antes de heurísticas de item; em seguida vêm editorial, item,
    entrada de arquivo e páginas institucionais. O objetivo é reduzir falsos itens
    sem ocultar rotas de item fortes em caminhos que também contêm vocabulário de
    arquivo ou catálogo.
    """

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
    query_keys = {key.casefold() for key in parse_qs(parts.query, keep_blank_values=True)}

    access_state, access_evidence = _access_state(
        fetch_status=fetch_status,
        title=title_norm,
        text=text_norm,
        metadata_text=metadata_norm,
    )

    specificity_score, specificity_evidence = _item_specificity(url, tokens, query_keys)
    catalogue_detail_route = (
        not is_root_surface
        and bool(token_set & _CATALOGUE_TOKENS)
        and specificity_score >= 2
    )
    audiovisual_fiche_route = "fiche" in token_set and bool(token_set & _AUDIOVISUAL_PATH_TOKENS)
    record_detail_route = bool(token_set & {"detail", "details", "record", "notice", "item"}) and specificity_score >= 2
    explicit_audiovisual_detail_route = _has_explicit_audiovisual_detail_route(parts.path)
    title_has_audiovisual_marker = any(
        marker in title_norm for marker in _AUDIOVISUAL_TITLE_MARKERS
    )
    structured_has_direct_audiovisual_object = any(
        marker in structured_norm
        for marker in (
            "videoobject",
            "audioobject",
            '"@type":"movie"',
            '"@type": "movie"',
        )
    )
    metadata_has_direct_audiovisual_media = any(
        marker in metadata_norm
        for marker in ("og:video", "og:audio", "twitter:player")
    )
    strong_structured_item = (
        specificity_score >= 2
        and (
            structured_has_direct_audiovisual_object
            or metadata_has_direct_audiovisual_media
        )
    )
    strong_item_route = (
        catalogue_detail_route
        or audiovisual_fiche_route
        or record_detail_route
        or (explicit_audiovisual_detail_route and title_has_audiovisual_marker)
        or strong_structured_item
    )

    if _looks_restricted_route(parts.path, token_set):
        return SurfaceTypeDecision(
            "restricted_or_unavailable",
            "medium",
            ("path:restricted-or-personal-area",),
            access_state,
            access_evidence,
        )

    search_evidence: list[str] = []
    search_score = 0
    search_path = sorted(token_set & _SEARCH_TOKENS)
    if search_path:
        search_score += 4
        search_evidence.append(f"path:{search_path[0]}")
    if query_keys & {"q", "query", "search", "keyword", "keywords", "term"}:
        search_score += 4
        search_evidence.append("query:search-parameter")
    if _has_facet_query(query_keys):
        search_score += 4
        search_evidence.append("query:facet-or-filter")
    search_title = _contains_any(title_norm, _SEARCH_TOKENS)
    if search_title:
        search_score += 2
        search_evidence.append(f"title:{search_title[0]}")

    if not strong_item_route:
        strong_text_marker = next(
            (marker for marker in _SEARCH_TEXT_MARKERS if marker in text_norm),
            None,
        )
        if strong_text_marker:
            search_score += 4
            search_evidence.append(f"text:{strong_text_marker}")
        structured_compact = structured_norm.replace(" ", "")
        if '"@type":"itemlist"' in structured_compact:
            search_score += 4
            search_evidence.append("structured:item-list")

    if is_root_surface and token_set & _CATALOGUE_TOKENS:
        search_score += 4
        search_evidence.append("root:catalogue-index")

    if "ajax" in token_set and token_set & _AJAX_INDEX_TOKENS:
        search_score += 4
        search_evidence.append("path:ajax-filter-index")

    archive_occurrences = sum(token in _ARCHIVE_TOKENS for token in tokens)
    if not strong_item_route:
        if not is_root_surface and archive_occurrences >= 2:
            search_score += 4
            search_evidence.append("path:nested-or-repeated-archive-index-context")
        if (
            not is_root_surface
            and bool(token_set & _ARCHIVE_TOKENS)
            and bool(token_set & _AUDIOVISUAL_PLURAL_PATH_TOKENS)
            and specificity_score < 2
        ):
            search_score += 4
            search_evidence.append("path:archive-audiovisual-browse-context")
        if not is_root_surface and "fonds" in title_norm:
            search_score += 4
            search_evidence.append("title:fund-or-fonds-index")

    if search_score >= 4:
        return SurfaceTypeDecision(
            "search_or_index",
            _confidence(search_score),
            tuple(search_evidence),
            access_state,
            access_evidence,
        )

    editorial_evidence: list[str] = []
    editorial_score = 0
    editorial_path = sorted(token_set & _EDITORIAL_PATH_TOKENS)
    if editorial_path:
        editorial_score += 4
        editorial_evidence.append(f"path:{editorial_path[0]}")
    if not strong_item_route and (
        "newsarticle" in structured_norm
        or '"@type":"article"' in structured_norm.replace(" ", "")
    ):
        editorial_score += 4
        editorial_evidence.append("structured:article")
    editorial_title = _contains_any(title_norm, _EDITORIAL_PATH_TOKENS)
    if editorial_title:
        editorial_score += 2
        editorial_evidence.append(f"title:{editorial_title[0]}")
    weak_editorial = sorted(token_set & _EDITORIAL_WEAK_TOKENS)
    if weak_editorial:
        editorial_score += 1
        editorial_evidence.append(f"path:weak-{weak_editorial[0]}")
    if _contains_any(title_norm, _EDITORIAL_WEAK_TOKENS):
        editorial_score += 1
        editorial_evidence.append("title:weak-press-context")
    if editorial_score >= 4:
        return SurfaceTypeDecision(
            "news_or_editorial",
            _confidence(editorial_score),
            tuple(editorial_evidence),
            access_state,
            access_evidence,
        )

    item_evidence: list[str] = []
    item_score = 0
    item_path = sorted(token_set & _ITEM_TOKENS)
    if item_path:
        item_score += 2
        item_evidence.append(f"path:{item_path[0]}")

    item_score += specificity_score
    item_evidence.extend(specificity_evidence)

    if catalogue_detail_route:
        item_score += 2
        item_evidence.append("path:catalogue-detail")
    if audiovisual_fiche_route:
        item_score += 2
        item_evidence.append("path:audiovisual-fiche")
    if record_detail_route:
        item_score += 1
        item_evidence.append("path:record-detail")
    if explicit_audiovisual_detail_route and title_has_audiovisual_marker:
        item_score += 3
        item_evidence.append("path:explicit-audiovisual-detail")
        item_evidence.append("title:audiovisual-marker")

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
    if any(marker in metadata_norm for marker in ("video_frames", "video-frame", "video frame")):
        media_score += 2
        media_evidence.append("metadata:audiovisual-frame")

    explicit_audiovisual_route = bool(token_set & _AUDIOVISUAL_PATH_TOKENS) and not bool(
        token_set & _RECORDISH_PATH_TOKENS
    )
    sufficiently_specific = specificity_score >= 2 or item_score >= 6
    if item_score >= 4 and (media_score >= 2 or (explicit_audiovisual_route and sufficiently_specific)):
        return SurfaceTypeDecision(
            "audiovisual_item",
            _confidence(item_score + media_score, high_at=7),
            tuple(item_evidence + media_evidence),
            access_state,
            access_evidence,
        )
    if item_score >= 4:
        return SurfaceTypeDecision(
            "item_record",
            _confidence(item_score),
            tuple(item_evidence),
            access_state,
            access_evidence,
        )

    archive_evidence: list[str] = []
    archive_score = 0
    archive_path = sorted(token_set & _ARCHIVE_TOKENS)
    if archive_path:
        archive_score += 2
        archive_evidence.append(f"path:{archive_path[0]}")
    archive_title = _contains_any(title_norm, _ARCHIVE_TOKENS)
    if archive_title:
        archive_score += 2
        archive_evidence.append(f"title:{archive_title[0]}")
    if any(
        phrase in text_norm
        for phrase in (
            "browse the collection",
            "explore the collection",
            "explorer les archives",
            "consultar o acervo",
        )
    ):
        archive_score += 1
        archive_evidence.append("text:archive-navigation")
    if archive_score >= 4:
        return SurfaceTypeDecision(
            "archive_landing_page",
            _confidence(archive_score),
            tuple(archive_evidence),
            access_state,
            access_evidence,
        )

    if is_root_surface:
        return SurfaceTypeDecision(
            "homepage",
            "high" if parts.path in {"", "/"} else "medium",
            ("observation_root_surface",),
            access_state,
            access_evidence,
        )

    if _same_host_and_under_root(url, root_url) and (urlsplit(root_url).path or "/") not in {"", "/"}:
        return SurfaceTypeDecision(
            "institutional_landing_page",
            "medium",
            ("descendant:institutional-observation-root",),
            access_state,
            access_evidence,
        )

    if any(
        marker in combined_meta
        for marker in (
            "about us",
            "about the",
            "qui sommes-nous",
            "a propos",
            "sobre nos",
            "sobre nós",
            "our mission",
            "notre mission",
        )
    ):
        return SurfaceTypeDecision(
            "institutional_landing_page",
            "low",
            ("metadata:institutional-context",),
            access_state,
            access_evidence,
        )

    if access_state in {"request_error", "http_error"}:
        return SurfaceTypeDecision(
            "restricted_or_unavailable",
            "medium",
            ("semantic-role:not-recoverable",),
            access_state,
            access_evidence,
        )

    return SurfaceTypeDecision("unknown", "low", (), access_state, access_evidence)


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
    "SURFACE_TYPING_PROTOCOL_VERSION",
    "SurfaceAccessState",
    "SurfaceConfidence",
    "SurfaceType",
    "SurfaceTypeDecision",
    "classify_surface_mapping",
    "classify_surface_type",
]
