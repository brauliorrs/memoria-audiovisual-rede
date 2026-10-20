"""Fail-closed public reader for approved MAR KAVI metadata-link batches.

Publishing record metadata to the MAR search interface does not activate
a completed custodian corpus or authorize any playback, proxy or media reuse.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from .kavi_finna_mar_index import _safe_record_link

CATALOG_FILENAME = "kavi_mar_metadata_links.csv"
MANIFEST_FILENAME = "kavi_mar_metadata_links_manifest.json"
VERSION = "kavi-mar-metadata-publication-1.0"
SHA256 = re.compile(r"^[a-f0-9]{64}$")


class PublicationRejected(ValueError):
    """Publication safety contract failed. Do not display untrusted data."""


def load_published_kavi_rows(output_dir: str | Path) -> tuple[list[dict], dict]:
    """Validate the provenance and link-only policy before presenting a batch."""
    root = Path(output_dir)
    m = root / MANIFEST_FILENAME
    c = root / CATALOG_FILENAME
    if not m.is_file() and not c.is_file():
        return [], {}
    if not (m.is_file() and c.is_file()):
        raise PublicationRejected("manifest_or_catalog_missing")
    try:
        manifest = json.loads(m.read_text(encoding="utf-8"))
        raw = c.read_bytes()
    except (OSError, ValueError) as ex:
        raise PublicationRejected("published_catalog_unreadable") from ex
    if not isinstance(manifest, dict) or any([
        manifest.get("schema_version") != VERSION,
        manifest.get("unit_id") != "fiaf-kavi",
        manifest.get("status") != "published_partial_metadata",
        manifest.get("coverage_status") != "partial",
        manifest.get("metadata_license") != "CC0-1.0_API_metadata_only",
        manifest.get("metadata_publication_approved") is not True,
        manifest.get("corpus_activation") is not False,
        manifest.get("media_downloaded") is not False,
        manifest.get("viewing_at_origin_only") is not True,
    ]):
        raise PublicationRejected("publication_state_invalid")
    digest = manifest.get("catalog_sha256")
    scope = manifest.get("source_scope_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise PublicationRejected("catalog_digest_missing")
    if not isinstance(scope, str) or not SHA256.fullmatch(scope):
        raise PublicationRejected("scope_digest_missing")
    if hashlib.sha256(raw).hexdigest() != digest:
        raise PublicationRejected("catalog_integrity_failure")
    total = manifest.get("expected_total_api_index")
    count = manifest.get("record_count")
    links = manifest.get("item_links_present")
    if (not isinstance(total, int) or isinstance(total, bool) or total <= 0
            or not isinstance(count, int) or isinstance(count, bool)
            or not isinstance(links, int) or isinstance(links, bool)
            or not 0 < count <= total or links != count):
        raise PublicationRejected("publication_counts_invalid")
    if not str(manifest.get("source_run_url", "")).startswith(
        "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/"
    ):
        raise PublicationRejected("publication_source_not_auditable")
    try:
        text = raw.decode("utf-8-sig")
        from io import StringIO
        reader = csv.DictReader(StringIO(text))
        needed = {
            "corpus", "source_record_id", "video_title", "video_link",
            "source_record_url", "metadata_provider", "metadata_license",
            "media_rights_status", "custody_status", "film_semantics",
            "scope_sha256", "link_status", "record_review_status",
        }
        if not needed.issubset(reader.fieldnames or []):
            raise PublicationRejected("published_columns_missing")
        rows = list(reader)
    except (ValueError, UnicodeError, csv.Error) as ex:
        raise PublicationRejected("published_csv_invalid") from ex
    if len(rows) != count:
        raise PublicationRejected("published_count_mismatch")
    seen = set()
    for row in rows:
        rid = row["source_record_id"]
        url = row["video_link"]
        if (not rid or rid in seen
                or row["corpus"] != "fiaf-kavi"
                or row["metadata_provider"] != "0/KAVI/"
                or row["metadata_license"] != "CC0-1.0_API_metadata_only"
                or row["media_rights_status"] != "not_verified"
                or row["custody_status"] != "not_established"
                or row["record_review_status"] != "unreviewed"
                or row["film_semantics"] not in (
                    "film_candidate", "unverified_audiovisual_record"
                )
                or row["link_status"] != "item_link_verified_by_source"
                or row["scope_sha256"] != scope
                or not row["video_title"]
                or row["source_record_url"] != url
                or _safe_record_link(url, rid) != url):
            raise PublicationRejected("published_record_invalid")
        seen.add(rid)
    return rows, manifest
