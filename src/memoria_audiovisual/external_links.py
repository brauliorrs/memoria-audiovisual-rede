"""Conservative external navigation links for MAR's metadata-only UI.

Never fetch or embed the linked resource. Untrusted non-HTTP(S) schemes,
credentials, control characters and invalid host whitespace are rejected.
Legacy spaces in URL paths/queries are percent-encoded only for navigation.
"""
from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import parse_qsl, unquote, urlsplit

# Media streams are not permanent record pages. Opening them can produce
# direct browser playback/download outside a custodian's contextual portal.
_MEDIA_SUFFIXES = (
    ".mp4", ".m4v", ".mov", ".webm", ".mkv", ".avi", ".flv",
    ".m3u8", ".mpd", ".wmv", ".mpg", ".mpeg", ".ts",
    ".mp3", ".wav", ".m4a", ".ogg",
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
    # Legacy media URLs often place the filename in a query parameter,
    # e.g. wwwopac.ashx?value=AV015929.mp4. Inspect VALUES, not a bare
    # query substring, to avoid false positives from normal search URLs.
    for _, value in parse_qsl(parsed.query, keep_blank_values=True):
        if unquote(value).split("?", 1)[0].casefold().endswith(_MEDIA_SUFFIXES):
            return True
    return False


def choose_origin_destination(
    discovered_url: object,
    institution_page_url: object = None,
    *,
    media_type: object = None,
) -> OriginDestination:
    """Favor an origin record/platform page, never a raw media stream.

    When the only item link is a raw file, fall back to the institution's
    public landing/catalog page, accurately labeled as a general page.
    No HTTP requests, ownership inferences or URL rewriting of the stored
    source evidence occur.
    """
    candidate = public_external_url(discovered_url)
    if candidate is not None and not is_direct_media_asset(candidate, media_type):
        return OriginDestination(candidate, "record_or_platform")
    fallback = public_external_url(institution_page_url)
    if fallback is not None and not is_direct_media_asset(fallback):
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
