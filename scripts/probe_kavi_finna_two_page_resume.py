"""One bounded two-page KAVI/Finna resume validation; no corpus admission.

All raw metadata, provider identifiers and opaque cursors remain in a disposable
local directory. The returned report is safe to publish as CI evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from memoria_audiovisual.config import HEADERS
from memoria_audiovisual.kavi_elonet_probe import USER_AGENT
from memoria_audiovisual.kavi_finna_adapter import FinnaMetadataSource, FinnaScope
from memoria_audiovisual.metadata_staging import (
    MetadataPageSource,
    StageRejected,
    public_stage_summary,
    stage_metadata,
)


def _audit_normalized_rows(
    directory: Path, manifest: dict[str, Any], source: MetadataPageSource,
) -> dict[str, Any]:
    """Inspect the locally hashed raw artifacts without exposing record IDs."""
    expected_code = source.scope.get("building_code")
    candidate_count = 0
    unverified_count = 0
    formats_unconfirmed = 0
    seen_ids: set[str] = set()
    record_digest = hashlib.sha256()
    for entry in manifest["pages"]:
        artifact_hash = entry["artifact_sha256"]
        if not isinstance(artifact_hash, str) or len(artifact_hash) != 64:
            raise StageRejected("audit_invalid_artifact_digest")
        artifact_path = directory / "raw" / artifact_hash[:2] / (artifact_hash + ".json")
        data = artifact_path.read_bytes()
        if hashlib.sha256(data).hexdigest() != artifact_hash:
            raise StageRejected("audit_artifact_integrity_failure")
        item = json.loads(data)
        source_response = item["page"]["source_response"]
        records = item["page"]["records"]
        source_ids = [
            row.get("id") for row in source_response.get("records", [])
        ]
        record_ids = [row.get("id") for row in records]
        if source_ids != record_ids:
            raise StageRejected("audit_source_to_normalized_ids_mismatch")
        if item["page"]["total"] != manifest["expected_total"]:
            raise StageRejected("audit_page_total_mismatch")
        for row in records:
            identity = row["id"]
            if identity in seen_ids:
                raise StageRejected("audit_duplicate_record_id")
            seen_ids.add(identity)
            record_digest.update(identity.encode("utf-8"))
            record_digest.update(b"\n")
            if (
                row.get("provider_index_code") != expected_code
                or row.get("custody_status") != "not_established"
                or row.get("media_rights_status") != "not_verified"
                or row.get("media_downloaded") is not False
            ):
                raise StageRejected("audit_provenance_or_rights_violation")
            if identity.startswith("kavi.elonet_elokuva_"):
                candidate_count += 1
                if row.get("film_semantics") != "film_candidate":
                    raise StageRejected("audit_film_classification_mismatch")
            else:
                unverified_count += 1
                if row.get("film_semantics") != "unverified_audiovisual_record":
                    raise StageRejected("audit_unverified_classification_mismatch")
            formats = row.get("formats")
            if not isinstance(formats, list) or not any(
                isinstance(f, dict) and f.get("value") == "0/Video/"
                for f in formats
            ):
                formats_unconfirmed += 1
    if len(seen_ids) != manifest["record_count"]:
        raise StageRejected("audit_record_count_mismatch")
    return {
        "record_id_sequence_sha256": record_digest.hexdigest(),
        "film_id_candidates": candidate_count,
        "other_video_records": unverified_count,
        "video_format_unconfirmed_records": formats_unconfirmed,
        "custody_established_records": 0,
        "media_rights_verified_records": 0,
    }


def verify_two_pages(
    source: MetadataPageSource,
    directory: Path,
    *,
    resume_delay_seconds: float = 0.0,
    sleep_fn=time.sleep,
) -> dict[str, Any]:
    if not 0 <= resume_delay_seconds <= 60:
        raise ValueError("invalid_resume_delay")
    first = stage_metadata(source, directory, max_pages=1)
    if first["status"] != "partial" or len(first["pages"]) != 1:
        raise StageRejected("two_page_probe_first_page_not_partial")
    # Each stage_metadata invocation has only one page, so its *internal*
    # between-page throttle cannot fire. Throttle this resume boundary.
    if resume_delay_seconds:
        sleep_fn(resume_delay_seconds)
    second = stage_metadata(source, directory, max_pages=1, resume=True)
    if (
        len(second["pages"]) != 2
        or second["record_count"] <= first["record_count"]
        or second["expected_total"] != first["expected_total"]
        or second["scope_sha256"] != first["scope_sha256"]
    ):
        raise StageRejected("two_page_probe_continuation_invalid")
    if second.get("promotion_authorized") is not False:
        raise StageRejected("two_page_probe_promotion_not_blocked")
    if second.get("media_downloaded") is not False:
        raise StageRejected("two_page_probe_media_flag_invalid")
    audit = _audit_normalized_rows(directory, second, source)
    return {
        "first_page": public_stage_summary(first),
        "after_resume": public_stage_summary(second),
        "resumption_verified": True,
        "integrity_audit": audit,
        "promotion_authorized": False,
        "media_downloaded": False,
        "note": "Two bounded pages only; not a complete catalogue enumeration.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bounded live two-page KAVI metadata resumption proof",
    )
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    scope = FinnaScope("0/KAVI/", "0/Video/", args.evidence_sha256)
    if not args.execute:
        print("DRY RUN: no API calls, no media and no corpus changes")
        return 0
    with requests.Session() as session, tempfile.TemporaryDirectory(
        prefix="kavi-finna-resume-"
    ) as folder:
        session.headers.update({
            **HEADERS,
            "User-Agent": f"{USER_AGENT}/1.0 (+metadata-integrity-probe)",
            "Accept": "application/json",
        })
        report = verify_two_pages(
            FinnaMetadataSource(session, scope),
            Path(folder),
            resume_delay_seconds=1.0,
        )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
