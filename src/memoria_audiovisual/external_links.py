"""Conservative external navigation links for MAR's metadata-only UI.

Never fetch or embed the linked resource. Untrusted non-HTTP(S) schemes,
credentials, control characters and invalid host whitespace are rejected.
Legacy spaces in URL paths/queries are percent-encoded only for navigation.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import parse_qsl, unquote, urlsplit

# Media streams are not permanent record pages. Opening them can produce
# direct browser playback/download outside a custodian's contextual portal.
_MEDIA_SUFFIXES = (
    ".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".flv",
    ".m3u8", ".mpd", ".wmv", ".mpg", ".mpeg", ".ts",
    ".mp3", ".wav", ".m4a", ".ogg",
)

# Only actual media-delivery query keys are considered; catalog searches
# with a lookfor=movie.mp4 term must continue to open the search page.
_MEDIA_QUERY_KEYS = frozenset({
    "value", "file", "filename", "media", "media_url", "mediaurl",
    "video", "video_url", "src", "source", "download", "asset", "path",
})

def _is_known_visitor_page(url: str) -> bool:
    """Fail-closed recognition of established public watch/record URL forms.

    An unfamiliar extensionless URL is NOT presumed safe: it may be a video
    delivery endpoint. The operator should discover a record-page route and
    prove its semantics before widening this list.
    """
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    if host in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        if path == "/watch":
            return any(k == "v" and bool(v) for k, v in parse_qsl(parsed.query))
        return path.startswith(("/shorts/", "/live/"))
    if host in ("youtu.be", "www.youtu.be"):
        return bool(path.strip("/")) and path.strip("/").count("/") == 0
    if host in ("vimeo.com", "www.vimeo.com"):
        segments = [x for x in path.split("/") if x]
        return bool(segments) and segments[-1].isdigit()
    if host in ("dailymotion.com", "www.dailymotion.com"):
        return path.startswith("/video/")
    if host == "dai.ly":
        return bool(path.strip("/"))
    if host in ("archive.org", "www.archive.org"):
        return path.startswith("/details/")
    if host in ("finna.fi", "www.finna.fi", "elonet.finna.fi"):
        return path.startswith(("/record/", "/search/"))
    if host in ("www.europeana.eu", "europeana.eu"):
        return path.startswith("/en/item/")
    if host in ("www.ina.fr", "ina.fr"):
        return path.startswith("/ina-eclaire-actu/video/")
    if host == "cnasearch.public.lu":
        return path.startswith("/searchprofiles/run/")
    return _is_known_item_record_page(url)


def _is_known_item_record_page(url: str) -> bool:
    """Only declare an item-specific page when its route is evidenced."""
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    # The Murnau-Stiftung collector constructs /movie/<numeric-id> pages
    # as public film metadata permalinks (not media delivery URLs).
    if host in ("murnau-stiftung.de", "www.murnau-stiftung.de"):
        return re.fullmatch(r"/movie/[0-9]+/?", path) is not None
    # Image'Est publishes individual documentary fiche pages in its
    # robots-declared sitemap. Preserve the exact public item link.
    if host in ("image-est.fr", "www.image-est.fr"):
        return re.fullmatch(r"/fiche-documentaire-[^/?#]+\.html", path) is not None
    if host in ("memobase.ch", "www.memobase.ch"):
        return path.startswith("/object/") and bool(path[len("/object/"):].strip("/"))
    # Collector-vetted ECPAD public Arkothèque item detail URL.
    if host == "archives.ecpad.fr" and path == "/archives/consulter-les-archives-en-ligne":
        return any(
            key.casefold() == "detail" and value.isdigit()
            for key, value in parse_qsl(parsed.query)
        )
    # Arkaader collector creates this public film/broadcast landing page;
    # /embed/ and /api/ routes must not be used as visitor destinations.
    if host in ("arkaader.ee", "www.arkaader.ee"):
        return bool(
            re.fullmatch(r"/landing/bc/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", parsed.path)
        )
    if host in ("www.cinemateca.pt", "cinemateca.pt") and path.endswith("/ficha.aspx"):
        values = dict((key.casefold(), value.casefold()) for key, value in parse_qsl(parsed.query))
        return values.get("obraid", "").isdigit() and values.get("type") == "video"
    if host in ("gosfilmofond.ru", "www.gosfilmofond.ru"):
        return path.startswith("/films/") and bool(path[len("/films/"):].strip("/"))
    if host == "film.iwmcollections.org.uk":
        return path.startswith("/record/") and bool(path[len("/record/"):].strip("/"))
    if host in ("cinememoire.net", "www.cinememoire.net") and path == "/notice":
        return any(
            key.casefold() == "num_seq" and value.isdigit()
            for key, value in parse_qsl(parsed.query)
        )
    # A generic /record/ path is not authoritative evidence of a catalog:
    # on unreviewed hosts it may itself be an opaque media-delivery route.
    return False


def _memobase_record_public_page(value: object) -> str | None:
    """Resolve the provider-documented API record ID to its visitor page.

    Memobase's own API documentation specifies that /record/<id> identifiers
    map to https://memobase.ch/object/<id>. Never use this mapping for
    arbitrary hosts or opaque relative paths, and do not mutate stored URLs.
    """
    candidate = public_external_url(value)
    if candidate is None:
        return None
    parsed = urlsplit(candidate)
    if (parsed.hostname or "").casefold() != "api.memobase.ch":
        return None
    match = re.fullmatch(r"/record/([A-Za-z0-9_-]+)", parsed.path)
    if match is None or match.group(1).casefold() in ("search",):
        return None
    # A search endpoint may have /record/search?q=...; an item link
    # can only carry the documented representation selector.
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() != "format" or value.casefold() not in (
            "json", "jsonld", "html",
        ):
            return None
    return f"https://memobase.ch/object/{match.group(1)}"


def _is_nontechnical_landing_page(value: object) -> bool:
    """Avoid sending a visitor to a metadata API or raw asset fallback."""
    safe = public_external_url(value)
    if safe is None or is_direct_media_asset(safe):
        return False
    parsed = urlsplit(safe)
    host = (parsed.hostname or "").casefold()
    path = parsed.path.casefold()
    return (
        not host.startswith(("api.", "data."))
        and "/wp-json/" not in path
        and not path.startswith(("/api/", "/graphql/"))
        and not path.endswith((".json", ".jsonld", ".xml", ".csv"))
    )


@dataclass(frozen=True)
class OriginDestination:
    url: str | None
    kind: str  # "record_or_platform", "institution_home", or "unavailable"


def is_direct_media_asset(url: object, media_type: object = None) -> bool:
    """Recognize known direct media URLs without a network request.

    MIME evidence is authoritative only when carried in a *separate* typed
    metadata field, not inferred from free-text film descriptions. Also
    recognize provider media-delivery routes without file extensions and
    query-style direct file names in known legacy source URLs.
    """
    if isinstance(media_type, str):
        reported_type = media_type.partition(";")[0].strip().casefold()
        if reported_type.startswith(("video/", "audio/")) or reported_type in (
            "application/vnd.apple.mpegurl",
            "application/x-mpegurl",
            "application/dash+xml",
        ):
            return True

    safe_url = public_external_url(url)
    if safe_url is None:
        return False
    parsed = urlsplit(safe_url)
    path = unquote(parsed.path).casefold()
    if path.endswith(_MEDIA_SUFFIXES):
        return True
    # Confirmed CNA direct video route, e.g. cna.kiss.lu/getMedium/<hash>.
    # Such URLs have no suffix but are media endpoints, not catalogue pages.
    if parsed.hostname and parsed.hostname.casefold() == "cna.kiss.lu":
        if path.startswith("/getmedium/"):
            return True
    # Memobase LOD digitalObject locators are technical media routes rather
    # than playable public record pages, even without file extensions.
    if parsed.hostname and parsed.hostname.casefold() == "prod.media.memobase.ch":
        if path.startswith("/memo/"):
            return True
    # Infomaniak's single-item VOD URLs are delivery routes (Autrefois
    # corpus), not ordinary institutional item records.
    if parsed.hostname and parsed.hostname.casefold() == "play.vod2.infomaniak.com":
        if path.startswith("/single/"):
            return True
    # Legacy media URLs often place the filename in a query parameter,
    # e.g. wwwopac.ashx?value=AV015929.mp4. Inspect VALUES, not a bare
    # query substring, to avoid false positives from normal search URLs.
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.casefold() not in _MEDIA_QUERY_KEYS:
            continue
        if unquote(value).split("?", 1)[0].casefold().endswith(_MEDIA_SUFFIXES):
            return True
    return False


def choose_origin_destination(
    discovered_url: object,
    institution_page_url: object = None,
    *,
    record_page_url: object = None,
    media_type: object = None,
) -> OriginDestination:
    """Favor an origin record/platform page, never a raw media stream.

    An unfamiliar technical-looking URL is not treated as a public
    watch page merely because it lacks a file extension. Prefer item-record
    evidence, then a source catalog landing page with an explicit disclaimer.
    No HTTP requests, ownership inferences or URL rewriting of the stored
    source evidence occur.
    """
    candidate = public_external_url(discovered_url)
    if (
        candidate is not None
        and not is_direct_media_asset(candidate, media_type)
        and _is_known_visitor_page(candidate)
    ):
        return OriginDestination(candidate, "record_or_platform")
    # The collector may already provide an item-specific *record* as its
    # partner_site. Prefer it to the unit-wide catalog landing page.
    # Prefer the documented human-facing Memobase page over its JSON API.
    item_page = (
        _memobase_record_public_page(record_page_url)
        or public_external_url(record_page_url)
    )
    if (
        item_page is not None
        and _is_nontechnical_landing_page(item_page)
        and _is_known_visitor_page(item_page)
    ):
        return OriginDestination(
            item_page,
            "record_or_platform" if _is_known_item_record_page(item_page)
            else "institution_home",
        )
    fallback = public_external_url(institution_page_url)
    if fallback is not None and _is_nontechnical_landing_page(fallback):
        return OriginDestination(fallback, "institution_home")
    return OriginDestination(None, "unavailable")



def public_external_url(value: object) -> str | None:
    """Return a safe absolute HTTP(S) link without making network requests."""
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if len(value) > 4096 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    # Historical cinema snapshots contain legitimate unencoded spaces in
    # paths (FAR, BArch, Ciné-Archives, CNC-AFF). Encode spaces for navigation
    # without mutating the preserved source URL in the corpus.
    if any(char.isspace() and char != " " for char in value):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Force validation of malformed numeric port.
    except ValueError:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if " " in parsed.netloc or "\\" in value:
        return None
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return None
    if port is not None and not 1 <= port <= 65535:
        return None
    # The link destination is a derived navigation URL, not a replacement
    # for the original source identifier recorded in the MAR snapshot.
    return value.replace(" ", "%20")
