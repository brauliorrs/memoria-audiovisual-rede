"""Offline, fail-closed G4 evidence gate for KAVI/Kuvi metadata corpus.

Only checks consistency and readiness for INDEPENDENT HUMAN REVIEW.
Never runs a network request, admits records, changes MAR production, or
interprets video availability/ownership from a Finna provider facet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

# Make the shared survey URL validator importable when invoked as a CLI path.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_public_access_survey import _public_url as _reviewable_url

VERSION = "mar-kavi-admission-evidence-1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
APPROVED_STATES = {"hold_provisional", "ready_for_human_review"}
CANDIDATE_SCOPE = "provider_video_index"
EXPECTED_PROVIDER = "0/KAVI/"
EXPECTED_FORMAT = "0/Video/"


def _dictionary(parent: dict, key: str, errors: list[str]) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"invalid_{key}_object")
        return {}
    return value


def _integer(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _public_url(value: object) -> bool:
    # Reuse the project's hardened public-host validation, including refusal
    # of loopback, private, multicast, numeric aliases and malformed hosts.
    if not isinstance(value, str) or len(value) > 2048:
        return False
    return _reviewable_url(value) and urlsplit(value).scheme == "https"


def _date(value: object) -> bool:
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def evaluate(dossier: object) -> dict[str, object]:
    """Return an auditable rejection or HOLD/READY decision; NEVER 'admitted'."""
    invalid: list[str] = []
    hold: list[str] = []
    if not isinstance(dossier, dict):
        return {"status": "REJECT_INVALID_EVIDENCE", "reasons": ["not_object"],
                "promotion_authorized": False}
    for key in ("schema_version", "unit_id", "declared_state"):
        if not isinstance(dossier.get(key), str):
            invalid.append(f"invalid_{key}")
    if dossier.get("schema_version") != VERSION:
        invalid.append("schema_version_mismatch")
    if dossier.get("unit_id") != "fiaf-kavi":
        invalid.append("incorrect_unit_id")
    if dossier.get("declared_state") not in APPROVED_STATES:
        invalid.append("unsupported_admission_state")

    scope = _dictionary(dossier, "scope", invalid)
    snapshot = _dictionary(dossier, "snapshot", invalid)
    quality = _dictionary(dossier, "source_quality", invalid)
    governance = _dictionary(dossier, "governance", invalid)

    expected_scope = {
        "provider_code": EXPECTED_PROVIDER,
        "format_code": EXPECTED_FORMAT,
        "scope_definition": CANDIDATE_SCOPE,
        "metadata_license": "CC0-1.0",
        "media_policy": "origin_link_only",
        "api_endpoint": "https://api.finna.fi/v1/search",
    }
    for field, required in expected_scope.items():
        if scope.get(field) != required:
            invalid.append(f"unapproved_scope_{field}")

    for key in ("scope_sha256", "record_id_sequence_sha256", "artifact_sha256"):
        if not isinstance(snapshot.get(key), str) or not SHA256.fullmatch(
            snapshot[key]
        ):
            invalid.append(f"invalid_{key}")
    for key in ("evidence_url",):
        if not _public_url(snapshot.get(key)):
            invalid.append(f"invalid_snapshot_{key}")
    if not _date(snapshot.get("observed_on")):
        invalid.append("invalid_observed_on")
    counts = ("expected_total", "distinct_record_count", "page_count",
              "duplicate_ids", "missing_records")
    for key in counts:
        if not _integer(snapshot.get(key)):
            invalid.append(f"invalid_snapshot_{key}")
    if snapshot.get("completeness") not in ("partial", "complete"):
        invalid.append("invalid_snapshot_completeness")
    for key in ("terminal_cursor_exhausted", "offline_integrity_verified",
                "snapshot_freshness_verified"):
        if type(snapshot.get(key)) is not bool:
            invalid.append(f"invalid_snapshot_{key}")

    for key in ("film_id_candidates", "other_video_records",
                "human_film_classification_reviewed",
                "provenance_labeled_records", "custody_labeled_records",
                "media_access_labeled_records"):
        if not _integer(quality.get(key)):
            invalid.append(f"invalid_quality_{key}")
    for key in ("sampling_plan_url", "curatorial_review_evidence_url",
                "per_record_audit_evidence_url"):
        if quality.get(key) is not None and not _public_url(quality.get(key)):
            invalid.append(f"invalid_quality_{key}")
    digest = quality.get("per_record_audit_sha256")
    if digest is not None and (not isinstance(digest, str)
                               or not SHA256.fullmatch(digest)):
        invalid.append("invalid_per_record_audit_sha256")

    reviewers = governance.get("independent_reviewers")
    if not isinstance(reviewers, list) or any(
        not isinstance(n, str) or not n.strip() or len(n) > 100
        for n in reviewers
    ):
        invalid.append("invalid_independent_reviewers")
        reviewers = []
    if len(reviewers) != len(set(reviewers)):
        invalid.append("duplicate_independent_reviewers")
    if governance.get("review_document_url") is not None and not _public_url(
        governance.get("review_document_url")
    ):
        invalid.append("invalid_review_document_url")
    if governance.get("review_status") not in ("not_started", "completed"):
        invalid.append("invalid_review_status")
    if governance.get("corpus_activation") is not False:
        invalid.append("corpus_activation_prohibited")

    if invalid:
        return {"status": "REJECT_INVALID_EVIDENCE",
                "reasons": sorted(set(invalid)), "promotion_authorized": False}

    total = snapshot["expected_total"]
    count = snapshot["distinct_record_count"]
    if count > total:
        return {"status": "REJECT_INVALID_EVIDENCE",
                "reasons": ["observed_exceeds_expected_total"],
                "promotion_authorized": False}
    if quality["film_id_candidates"] + quality["other_video_records"] != count:
        return {"status": "REJECT_INVALID_EVIDENCE",
                "reasons": ["candidate_class_counts_do_not_match_observed"],
                "promotion_authorized": False}
    if quality["human_film_classification_reviewed"] > count:
        invalid.append("human_review_exceeds_observed")
    for key in ("provenance_labeled_records", "custody_labeled_records",
                "media_access_labeled_records"):
        if quality[key] > count:
            invalid.append(f"{key}_exceeds_observed")
    if snapshot["page_count"] == 0 and count > 0:
        invalid.append("records_without_pages")
    if invalid:
        return {"status": "REJECT_INVALID_EVIDENCE",
                "reasons": sorted(set(invalid)), "promotion_authorized": False}

    if snapshot["completeness"] != "complete":
        hold.append("partial_enumeration")
    if count != total:
        hold.append("incomplete_record_coverage")
    if not snapshot["terminal_cursor_exhausted"]:
        hold.append("terminal_cursor_unverified")
    if not snapshot["offline_integrity_verified"]:
        hold.append("offline_integrity_unverified")
    if not snapshot["snapshot_freshness_verified"]:
        hold.append("snapshot_freshness_unverified")
    if snapshot["duplicate_ids"] != 0 or snapshot["missing_records"] != 0:
        hold.append("duplicate_or_missing_records")
    if quality["human_film_classification_reviewed"] == 0:
        hold.append("human_film_semantics_unreviewed")
    for key in ("sampling_plan_url", "curatorial_review_evidence_url",
                "per_record_audit_evidence_url", "per_record_audit_sha256"):
        if not quality.get(key):
            hold.append(f"missing_{key}")
    # "Labeled" requires an explicitly recorded status, including 'unknown',
    # NOT proven ownership or media reuse rights for every work.
    for key in ("provenance_labeled_records", "custody_labeled_records",
                "media_access_labeled_records"):
        if quality[key] != count:
            hold.append(f"incomplete_{key}")
    if len(reviewers) < 2 or governance["review_status"] != "completed":
        hold.append("independent_review_incomplete")
    if not governance.get("review_document_url"):
        hold.append("review_document_missing")

    status = "HOLD_PROVISIONAL" if hold else "READY_FOR_HUMAN_ADJUDICATION"
    if (dossier["declared_state"] == "ready_for_human_review"
            and status != "READY_FOR_HUMAN_ADJUDICATION"):
        hold.append("unsupported_ready_declaration")
    if dossier["declared_state"] == "hold_provisional" and not hold:
        status = "HOLD_PROVISIONAL"
        hold.append("explicit_hold_not_promoted")
    return {"status": status, "reasons": sorted(set(hold)),
            "observed_records": count, "reference_total": total,
            "completeness": snapshot["completeness"],
            "promotion_authorized": False}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OFFLINE KAVI G4 evidence gate")
    parser.add_argument("dossier", type=Path)
    args = parser.parse_args(argv)
    try:
        dossier = json.loads(args.dossier.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print(json.dumps({"status": "REJECT_INVALID_EVIDENCE",
                          "reasons": ["unreadable_dossier"],
                          "promotion_authorized": False}))
        return 2
    result = evaluate(dossier)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 2 if result["status"] == "REJECT_INVALID_EVIDENCE" else 0


if __name__ == "__main__":
    raise SystemExit(main())
