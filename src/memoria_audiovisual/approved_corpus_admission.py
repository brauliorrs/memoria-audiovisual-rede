"""Fail-closed, offline admission of *additional* approved origin-record fiches.

This module does not approve publications. A reviewed manifest and CSV must
exist for each corpus; otherwise it admits zero records. Never downloads media.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from .corpus_admission_engine import COMMON_FIELDS, REGISTRY, ContractRejected, connector_for

VERSION = "mar-approved-origin-fiches-v1"
MAX_CATALOG_BYTES = 5 * 1024 * 1024
MAX_RECORDS = 1000
# The vetted institutional hosts and common metadata fields have one source of truth.
CORPUS_HOSTS = {code: spec.record_hosts for code, spec in REGISTRY.items()}
FIELDS = COMMON_FIELDS
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
DATE = re.compile(r"20[0-9]{2}-[01][0-9]-[0-3][0-9]\Z")
RUN = re.compile(
    r"https://github\.com/brauliorrs/memoria-audiovisual-rede/actions/runs/[1-9][0-9]*\Z"
)


class AdmissionRejected(ValueError):
    """Publication evidence is insufficient; keep this batch in HOLD."""


def _is_record_url(value: str, corpus: str) -> bool:
    if not isinstance(value, str) or value != value.strip() or "\\" in value:
        return False
    try:
        parsed = urlsplit(value)
        hostname, port = parsed.hostname, parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and hostname in CORPUS_HOSTS[corpus]
        and port in (None, 443)
        and parsed.username is None and parsed.password is None
        and bool(parsed.path.strip("/"))
        and not parsed.query and not parsed.fragment
        and not re.search(r"\.(mp4|m3u8|mpd|mov|webm|mkv|ts)$", parsed.path, re.I)
        and all(ord(ch) >= 32 for ch in value)
    )


def load_one_approved_corpus(root: str | Path, corpus: str) -> list[dict]:
    """Read one explicitly approved CSV+manifest pair; missing pair means HOLD/no rows."""
    try:
        connector_for(corpus)
    except ContractRejected as exc:
        raise AdmissionRejected("corpus_not_admitted") from exc
    base = Path(root) / "mar_admitted"
    csv_file = base / (corpus + ".csv")
    manifest_file = base / (corpus + ".manifest.json")
    if not csv_file.exists() and not manifest_file.exists():
        return []
    if not csv_file.is_file() or not manifest_file.is_file():
        raise AdmissionRejected("catalog_manifest_pair_missing")
    if csv_file.is_symlink() or manifest_file.is_symlink():
        raise AdmissionRejected("symlink_not_allowed")
    if csv_file.stat().st_size > MAX_CATALOG_BYTES:
        raise AdmissionRejected("catalog_too_large")
    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        content = csv_file.read_bytes()
    except (OSError, UnicodeError, ValueError) as exc:
        raise AdmissionRejected("admission_unreadable") from exc
    if not isinstance(manifest, dict):
        raise AdmissionRejected("manifest_invalid")
    sha = manifest.get("catalog_sha256")
    count = manifest.get("record_count")
    reviewer = manifest.get("reviewer")
    if (
        manifest.get("schema_version") != VERSION
        or manifest.get("corpus_code") != corpus
        or manifest.get("status") != "approved_public_metadata"
        or manifest.get("approved_for_publication") is not True
        or manifest.get("media_downloaded") is not False
        or manifest.get("viewing_at_origin_only") is not True
        or manifest.get("corpus_activation") is not False
        or not isinstance(reviewer, str) or not reviewer.strip()
        or not RUN.fullmatch(str(manifest.get("source_run_url", "")))
        or not DATE.fullmatch(str(manifest.get("observed_on", "")))
        or type(count) is not int or not 0 < count <= MAX_RECORDS
        or not isinstance(sha, str) or not HEX64.fullmatch(sha)
        or hashlib.sha256(content).hexdigest() != sha
    ):
        raise AdmissionRejected("publication_manifest_not_verified")
    try:
        decoded = content.decode("utf-8-sig")
        from io import StringIO
        reader = csv.DictReader(StringIO(decoded))
        if reader.fieldnames != list(FIELDS):
            raise AdmissionRejected("unexpected_catalog_columns")
        rows = list(reader)
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise AdmissionRejected("published_catalog_unreadable") from exc
    if len(rows) != count:
        raise AdmissionRejected("catalog_count_mismatch")
    seen_ids: set[str] = set()
    seen_urls: set[str] = set()
    admitted: list[dict] = []
    for row in rows:
        rid = row.get("source_record_id")
        url = row.get("source_record_url")
        title = row.get("video_title")
        if (
            not isinstance(rid, str) or not rid or len(rid) > 220
            or rid in seen_ids or not _is_record_url(url, corpus)
            or url in seen_urls or not title or len(title) > 600
            or row.get("media_access_status") != "unverified"
            or row.get("media_rights_status") != "not_verified"
            or row.get("record_review_status") != "approved_metadata_only"
            or any(v is None or len(v) > 2000 for v in row.values())
        ):
            raise AdmissionRejected("approved_record_invalid")
        seen_ids.add(rid)
        seen_urls.add(url)
        admitted.append({
            **row,
            "source_service": "mar_admitted_metadata",
            "corpus_code": corpus,
            "video_link": url,
            "video_title_display": title,
            "video_date_display": row["year"],
            "video_theme": row["genres"] or row["subjects"],
            "video_subject": row["subjects"],
            "access_surface": "Ficha externa; reprodução não verificada",
            "access_regime": "metadados públicos; mídia não avaliada",
            "catalog_coverage": "approved_incremental_metadata_only",
            "catalog_observed_on": manifest["observed_on"],
        })
    return admitted


def load_all_approved_corpora(root: str | Path) -> dict[str, list[dict]]:
    """No fallback to existing raw CSV or scraping when approval is absent."""
    return {code: load_one_approved_corpus(root, code) for code in REGISTRY}
