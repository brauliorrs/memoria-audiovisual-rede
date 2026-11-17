"""Direct access to the previously published KAVI/Finna record-link index.

This module never reads unapproved CSVs directly, never downloads media,
never triggers collectors and never promotes institutional corpus status.
"""
from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from .kavi_finna_public_catalog import PublicationRejected, load_published_kavi_rows


RELEASE_MARKER = "MAR-KAVI-DIRECT-20261117"


class KaviAccessResult(NamedTuple):
    rows: list[dict]
    manifest: dict
    status: str


def read_kavi_direct_index(output_dir: str | Path) -> KaviAccessResult:
    """Load the signed public KAVI index or expose an explicit safe HOLD.

    The public catalog currently contains 200 approved-for-publication
    metadata fiches. The expected number is read from the authenticated
    manifest, not blindly invented or hard-coded into the runtime.
    """
    try:
        rows, manifest = load_published_kavi_rows(output_dir)
    except PublicationRejected:
        return KaviAccessResult([], {}, "hold_integrity")
    except (OSError, UnicodeError):
        return KaviAccessResult([], {}, "hold_unreadable")
    if not rows:
        return KaviAccessResult([], {}, "missing_release_assets")
    if not isinstance(manifest, dict) or manifest.get("record_count") != len(rows):
        return KaviAccessResult([], {}, "hold_count")
    return KaviAccessResult(rows, manifest, "published_partial_metadata")


def records_for_display(result: KaviAccessResult) -> list[dict]:
    """Minimal metadata columns and origin-only links, no media."""
    if result.status != "published_partial_metadata":
        return []
    return [
        {
            "Título": row.get("video_title", ""),
            "Ano": row.get("year", ""),
            "Assuntos": row.get("subjects", ""),
            "Identificador": row["source_record_id"],
            "Acessar ficha na origem": row["source_record_url"],
        }
        for row in result.rows
    ]
