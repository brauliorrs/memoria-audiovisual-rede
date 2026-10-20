"""Read-only, validated metadata-index status for registered KAVI/Kuvi corpus.

A catalog record link is NOT a playable video URL. Do not mix record counts
with global audiovisual playback metrics or enable scheduled network collection.
"""
from __future__ import annotations

from pathlib import Path

from .kavi_finna_public_catalog import load_published_kavi_rows


def load_kavi_metadata_index_summary(output_directory: str | Path) -> dict:
    """Return verified, descriptive counts; never activate media or corpus.

    Raises PublicationRejected if the on-disk index cannot pass its integrity
    and source-link checks. Empty if there is no published index.
    """
    rows, manifest = load_published_kavi_rows(output_directory)
    if not rows:
        return {}
    count = len(rows)
    link_count = sum(bool(row["source_record_url"]) for row in rows)
    reference = manifest["expected_total_api_index"]
    if count != manifest["record_count"] or link_count != count:
        raise AssertionError("kavi_publication_summary_inconsistent")
    return {
        "source_unit_id": "fiaf-kavi",
        "status": manifest["status"],
        "coverage_status": manifest["coverage_status"],
        "indexed_metadata_records": count,
        "source_record_links": link_count,
        "reference_total_api_video_index": reference,
        "reference_observed_on": manifest["observed_on"],
        "source_run_url": manifest["source_run_url"],
        "coverage_percent_of_api_snapshot": round(100 * count / reference, 4),
        "media_downloaded": False,
        "playable_video_count_verified": 0,
        "playback_verification_status": "unverified",
        "custody_status": "not_established",
        "corpus_activation": False,
        "automatic_refresh_enabled": False,
    }
