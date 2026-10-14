"""Conservative external navigation links for MAR's metadata-only UI.

Never fetch or embed the linked resource. Untrusted non-HTTP(S) schemes,
credentials, control characters and invalid host whitespace are rejected.
Legacy spaces in URL paths/queries are percent-encoded only for navigation.
"""
from __future__ import annotations

from urllib.parse import urlsplit


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
