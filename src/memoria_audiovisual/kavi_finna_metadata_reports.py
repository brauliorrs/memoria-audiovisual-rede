"""Deterministic KAVI/Kuvi documentary metadata reports, strictly offline.

Never turn Finna record-page links into playable video counts or infer
rights, custody, media availability or universe-wide audiovisual coverage.
Impact assessment and tests were committed before this module.
"""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

from .kavi_finna_public_catalog import (
    CATALOG_FILENAME,
    MANIFEST_FILENAME,
    PublicationRejected,
    load_published_kavi_rows,
)

REPORT_VERSION = "kavi-kuvi-documentary-metadata-analytics-1.0"
REPORT_FILES = {
    "summary": "kavi_kuvi_metadata_summary.csv",
    "field_coverage": "kavi_kuvi_metadata_field_coverage.csv",
    "semantics": "kavi_kuvi_metadata_semantics.csv",
    "report": "kavi_kuvi_metadata_report.json",
}
DESCRIPTIVE_FIELDS = (
    "video_title",
    "year",
    "authors",
    "genres",
    "subjects",
    "languages",
    "video_description",
)
SEMANTIC_CLASSES = (
    "film_candidate",
    "unverified_audiovisual_record",
)


def _has_value(row: dict, field: str) -> bool:
    value = row.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def build_kavi_metadata_reports(rows: list[dict], manifest: dict) -> dict:
    """Build metrics from previously validated metadata; reject inconsistent inputs.

    A film identifier prefix remains only an unreviewed candidate. Numeric
    zeros for *verified* playback/rights/custody mean zero verifications
    documented, not that audiovisual media do not exist or cannot be watched.
    """
    if not isinstance(rows, list) or not rows or not isinstance(manifest, dict):
        raise PublicationRejected("metadata_report_input_missing")
    count = len(rows)
    observed = manifest.get("observed_on")
    try:
        observed_valid = (
            isinstance(observed, str)
            and date.fromisoformat(observed).isoformat() == observed
        )
    except (ValueError, TypeError):
        observed_valid = False
    expected = manifest.get("expected_total_api_index")
    if (not observed_valid
            or manifest.get("unit_id") != "fiaf-kavi"
            or manifest.get("status") != "published_partial_metadata"
            or manifest.get("coverage_status") != "partial"
            or manifest.get("corpus_activation") is not False
            or manifest.get("media_downloaded") is not False
            or manifest.get("metadata_publication_approved") is not True
            or manifest.get("metadata_license") != "CC0-1.0_API_metadata_only"
            or not isinstance(expected, int) or isinstance(expected, bool)
            or not isinstance(manifest.get("record_count"), int)
            or manifest.get("record_count") != count
            or manifest.get("item_links_present") != count
            or count > expected or expected <= 0):
        raise PublicationRejected("metadata_report_source_contract_mismatch")
    identities: set[str] = set()
    semantic_counts: Counter[str] = Counter()
    for row in rows:
        if not isinstance(row, dict):
            raise PublicationRejected("metadata_report_record_not_object")
        identity = row.get("source_record_id")
        film_semantics = row.get("film_semantics")
        if (not isinstance(identity, str) or not identity
                or identity in identities
                or row.get("source_service") != "finna_api"
                or row.get("corpus") != "fiaf-kavi"
                or row.get("link_status") != "item_link_verified_by_source"
                or not row.get("video_link")
                or row.get("source_record_url") != row.get("video_link")
                or row.get("media_access_status") != "unverified"
                or row.get("media_rights_status") != "not_verified"
                or row.get("custody_status") != "not_established"
                or row.get("record_review_status") != "unreviewed"
                or film_semantics not in SEMANTIC_CLASSES
                or row.get("scope_sha256") != manifest.get("source_scope_sha256")):
            raise PublicationRejected("metadata_report_record_contract_mismatch")
        identities.add(identity)
        semantic_counts[film_semantics] += 1
    if len(identities) != count:
        raise PublicationRejected("metadata_report_duplicate_identity")

    summary = {
        "source_unit_id": "fiaf-kavi",
        "report_kind": "documentary_metadata_index",
        "coverage_status": "partial",
        "reference_observed_on": manifest["observed_on"],
        "indexed_metadata_records": count,
        "source_record_links": count,
        "reference_total_api_video_index": expected,
        "coverage_percent_of_api_snapshot": round(100 * count / expected, 4),
        "film_candidate_records": semantic_counts["film_candidate"],
        "unverified_audiovisual_record_count": semantic_counts[
            "unverified_audiovisual_record"
        ],
        "curatorially_reviewed_records": 0,
        "verified_playback_records": 0,
        "verified_media_rights_records": 0,
        "verified_custody_records": 0,
        "playback_evidence_status": "unverified",
        "media_rights_evidence_status": "unverified",
        "custody_evidence_status": "not_established",
    }
    field_coverage = []
    for field in DESCRIPTIVE_FIELDS:
        present = sum(1 for row in rows if _has_value(row, field))
        field_coverage.append({
            "field": field,
            "present": present,
            "missing": count - present,
            "denominator": count,
            "percent_present": round(100 * present / count, 4),
            "meaning": "field_filled_not_factually_verified",
        })
    semantics = [
        {"film_semantics": name, "total": semantic_counts[name],
         "review_status": "unreviewed"}
        for name in SEMANTIC_CLASSES
        if semantic_counts[name] > 0
    ]
    provenance = {
        "schema_version": REPORT_VERSION,
        "source_unit_id": "fiaf-kavi",
        "source_run_url": manifest["source_run_url"],
        "catalog_sha256": manifest["catalog_sha256"],
        "source_scope_sha256": manifest["source_scope_sha256"],
        "observation_date": manifest["observed_on"],
        "metadata_license": manifest["metadata_license"],
        "source_catalog_file": CATALOG_FILENAME,
        "source_manifest_file": MANIFEST_FILENAME,
        "media_downloaded": False,
        "corpus_activation": False,
        "streaming_links_exported": False,
        "snapshot_only": True,
    }
    return {
        "summary": summary,
        "field_coverage": field_coverage,
        "semantics": semantics,
        "provenance": provenance,
    }


def _csv_bytes(records: list[dict], columns: list[str]) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return handle.getvalue().encode("utf-8")


def serialize_kavi_metadata_reports(report: dict) -> dict[str, bytes]:
    """Serialize reproducibly; no clock/network access and no raw media URLs."""
    return {
        REPORT_FILES["summary"]: _csv_bytes(
            [report["summary"]], list(report["summary"])
        ),
        REPORT_FILES["field_coverage"]: _csv_bytes(
            report["field_coverage"],
            ["field", "present", "missing", "denominator", "percent_present",
             "meaning"],
        ),
        REPORT_FILES["semantics"]: _csv_bytes(
            report["semantics"],
            ["film_semantics", "total", "review_status"],
        ),
        REPORT_FILES["report"]: (
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8"),
    }


def write_kavi_metadata_reports(
    source_dir: str | Path, output_dir: str | Path,
) -> dict:
    """Validate source FIRST, then export derived files with atomic replacements.

    The source KAVI public catalog and its integrity manifest are never
    touched. No conventional video-catalog or playback metrics are written.
    """
    rows, manifest = load_published_kavi_rows(source_dir)
    report = build_kavi_metadata_reports(rows, manifest)
    files = serialize_kavi_metadata_reports(report)
    source = Path(source_dir).resolve()
    output = Path(output_dir).resolve()
    reserved = {CATALOG_FILENAME, MANIFEST_FILENAME}
    if any(name in reserved for name in files):
        raise PublicationRejected("metadata_report_overwrites_public_source")
    if not output.exists():
        output.mkdir(parents=True)
    if not output.is_dir():
        raise PublicationRejected("metadata_report_output_not_directory")

    # Stage in a temporary directory and atomically replace each derived
    # report. Source filenames remain different even when output==source.
    with tempfile.TemporaryDirectory(prefix=".kavi-metadata-", dir=output) as temp:
        staged = Path(temp)
        for name, data in files.items():
            (staged / name).write_bytes(data)
        for name in files:
            target = output / name
            if target.is_symlink():
                raise PublicationRejected("metadata_report_symlink_refused")
        for name in files:
            os.replace(staged / name, output / name)
    return report
