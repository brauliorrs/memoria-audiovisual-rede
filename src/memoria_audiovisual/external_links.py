"""Conservative external navigation links for MAR's metadata-only UI.

Never fetch or embed the linked resource. Untrusted non-HTTP(S) schemes,
credentials, control characters and URL whitespace are rejected.
"""
from __future__ import annotations

from urllib.parse import urlsplit


def public_external_url(value: object) -> str | None:
    """Return a safe absolute HTTP(S) link without making network requests."""
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if len(value) > 4096 or any(ord(char) < 32 or ord(char) == 127 for char in value):
        return None
    if any(char.isspace() for char in value):
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port  # Force validation of malformed numeric port.
    except ValueError:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        return None
    if port is not None and not 1 <= port <= 65535:
        return None
    # Do not silently correct or rewrite source identifiers.
    return value
