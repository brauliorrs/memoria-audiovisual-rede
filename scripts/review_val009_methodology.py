#!/usr/bin/env python3
"""Pre-execution, offline methodology screening of VAL-009's proposed entities.

This is documentary QA, NOT a replacement for an independent research
protocol reviewer. In particular, no test-literal can become a confirmed
HTTP visit, no prior MAR entity can become project-wide unseen, and this
module NEVER issues scientific permission to collect, freeze, or evaluate.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from audit_val009_exposure import (
    AuditError,
    audit_historical_checkout,
    validate_inventory,
)

BASE = Path(__file__).resolve().parents[1]
REVIEW_FILE = (
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_methodology_review_v2_3_draft.json"
)
INVENTORY_FILE = (
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_exposure_inventory_v2_3_draft.json"
)
EXPECTED_GROUPS = {
    "M3_classifier_regression_input": 9,
    "fake_HTTP_collector_transport_test": 9,
    "synthetic_Arkaader_platform_fixture": 1,
    "collector_parser_or_access_metadata_test": 3,
}
EXPECTED_ENTITIES = frozenset({
    "cinematek", "cinematheque-bretagne", "dr", "ert",
    "estonian_film_archive", "filmoteca_catalunya",
})
_SHA1 = re.compile(r"[0-9a-f]{40}\Z")
_PINNED = "4544bbc40e076cd7a81800a3c93ebbfb8efae5b2"


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(
        b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes())


def _require_blob(value: Any) -> None:
    if not isinstance(value, str) or not _SHA1.fullmatch(value):
        raise AuditError("Missing/invalid pinned Git blob digest")


def validate_methodology_structure(
    review: dict[str, Any], inventory: dict[str, Any],
    inventory_bytes: bytes,
) -> dict[str, Any]:
    validate_inventory(inventory)
    for k, expected in {
        "status": "draft_pending_independent_protocol_reviewer_signoff",
        "historical_repository_revision": _PINNED,
        "site_visits_performed": False,
        "predictions_generated": False,
        "human_independent_signoff_received": False,
        "scientific_seal_granted": False,
        "verified_proven_historical_urls": 137,
        "basis_inventory_path": INVENTORY_FILE,
    }.items():
        if review.get(k) != expected or type(review.get(k)) is not type(expected):
            raise AuditError(f"Methodological invariant changed: {k}")
    _require_blob(review.get("basis_inventory_git_blob_sha"))
    if git_blob_sha(inventory_bytes) != review["basis_inventory_git_blob_sha"]:
        raise AuditError("Source inventory diverged from reviewed Git blob")
    _require_blob(review.get("historical_protocol_git_blob_sha"))
    fixture = review["fixture_screening"]
    previous = inventory["nonvalidated_fixture_literals"]
    if (
        len(fixture) != 22 or len(previous) != 22
        or review["fixture_screening_scope"]["total"] != 22
        or review["fixture_screening_scope"]["full_test_literal_or_root"] != 15
        or review["fixture_screening_scope"][
            "concatenated_fragments_requiring_reconstruction"
        ] != 7
    ):
        raise AuditError("Changed scope of the 22 documentary literals")
    originals = {
        (p["source_path"], p["url"]):
        (p["source_sha256"], p["source_git_blob_sha"])
        for p in previous
    }
    if len(originals) != 22:
        raise AuditError("Duplicate baseline literal")
    seen: set[tuple[str, str]] = set()
    for row in fixture:
        key = (row["source_path"], row["literal_url"])
        if key in seen or key not in originals:
            raise AuditError("Added/duplicated/replaced test literal")
        seen.add(key)
        if (row["source_sha256"], row["source_git_blob_sha"]) != originals[key]:
            raise AuditError("Test literal evidence re-attributed")
        if (row["human_signoff"] != "pending"
                or row["auto_exclusion"] is not False
                or row["claimed_redirect_alias"] is not False
                or row["evidence"] !=
                "literal_in_pinned_repository_test_not_a_live_HTTP_record"):
            raise AuditError("Test literal improperly approved/promoted")
        source = row["source_path"]
        expected_group = {
            "tests/test_surface_typing.py": "M3_classifier_regression_input",
            "tests/test_ai_surface_discovery.py":
                "fake_HTTP_collector_transport_test",
            "tests/test_estonian_film_archive_collection.py":
                "synthetic_Arkaader_platform_fixture",
            "tests/test_cinearchives_collection.py":
                "collector_parser_or_access_metadata_test",
        }.get(source)
        if row["usage"] != expected_group:
            raise AuditError("Test literal misclassified")
        if row["url_expression_status"] not in {
            "fragment_of_concatenated_Python_expression",
            "complete_literal_or_root_used_in_test",
        }:
            raise AuditError("Unknown test URL expression completeness")
        if (
            row["url_expression_status"] ==
            "fragment_of_concatenated_Python_expression"
            and source != "tests/test_surface_typing.py"
        ):
            raise AuditError("Non-M3 fixture is incorrectly called a fragment")
        if not isinstance(row["proposed_disposition"], str):
            raise AuditError("Disposition missing")
    counts = Counter(row["usage"] for row in fixture)
    fragments = sum(
        row["url_expression_status"] ==
        "fragment_of_concatenated_Python_expression" for row in fixture
    )
    if seen != set(originals) or counts != EXPECTED_GROUPS or fragments != 7:
        raise AuditError("Missing/misallocated fixture screening")
    targets = review["proposed_entities_scope"]
    prior = targets["entities"]
    if (
        targets["count"] != 6
        or targets["strictly_project_wide_unseen_entities"] != 0
        or len(prior) != 6
        or {x["entity_id"] for x in prior} != EXPECTED_ENTITIES
        or len({x["entity_id"] for x in prior}) != 6
    ):
        raise AuditError("Incorrect prior MAR corpus entity audit")
    previous_targets = {
        (x["entity_id"], x["root_url"])
        for x in inventory[
            "proposed_validation_entrypoints_not_evidence_of_independent_exposure"
        ]
    }
    if {(x["entity_id"], x["proposed_root_url"]) for x in prior} != previous_targets:
        raise AuditError("Invented/replaced preregistered target roots")
    for row in prior:
        for name in ("snapshot_metadata_git_blob_sha", "internal_pages_git_blob_sha"):
            _require_blob(row.get(name))
        if (row["prior_pipeline_source_root_match"] is not True
                or row["conclusion"] !=
                "previously_processed_in_broader_MAR_before_M3_2_3_candidate"
                or row["approval"] != "hold_pending_methodology_reviewer_decision"
                or row["original_http_response_bytes_retained_or_authenticity_verified"]
                is not False
                or row["exact_prior_M3_blind_human_root_overlap_proven"] is not False
                or not row["snapshot_generated_at"].startswith("2026-0")):
            raise AuditError("Unsupported novelty/provenance approval")
    _require_blob(targets["special_prior_code_for_estonia"]["git_blob_sha"])
    if (review["independent_reviewer"] != {
            "status": "pending", "reviewer_id": None,
            "reviewed_at": None, "decision": None, "rationale": None,
        }
        or review["exclusions_status"]["proven_minimum"] != 137
        or review["exclusions_status"]["fixture_exact_additions_approved"] != 0
        or review["exclusions_status"]["aliases_demonstrated_from_legacy_requested_final"] != 0
        or any(review["gating"][k] is not True for k in (
            "freeze_blocked", "independent_collection_blocked",
            "prediction_release_blocked",
        ))):
        raise AuditError("Independent review or scientific gate was forged")
    return {
        "mode": "documentary_structure",
        "state": "HOLD_pending_independent_signoff",
        "proven_historical_urls": 137,
        "test_literals_screened": 22,
        "test_URL_fragments_requiring_reconstruction": 7,
        "proposed_entities_with_prior_MAR_corpus": 6,
        "project_wide_unseen_entities": 0,
        "science_authorized": False,
    }


def verify_at_historical_commit(
    review: dict[str, Any], inventory: dict[str, Any],
    inventory_bytes: bytes, historical_root: Path,
) -> dict[str, Any]:
    """Authenticates all original bytes against a pinned, exact Git checkout."""
    report = validate_methodology_structure(review, inventory, inventory_bytes)
    audit_historical_checkout(inventory, historical_root)
    protocol_path = historical_root / review["historical_protocol_path"]
    raw = protocol_path.read_bytes()
    if git_blob_sha(raw) != review["historical_protocol_git_blob_sha"]:
        raise AuditError("Old preregistration draft changed")
    protocol = json.loads(raw)
    protocol_targets = {
        x["entity_id"]: x["root_url"] for x in protocol["entities"]
    }
    prior_targets = review["proposed_entities_scope"]["entities"]
    if len(protocol_targets) != 6:
        raise AuditError("Original target population differs")
    for target in prior_targets:
        eid, root = target["entity_id"], target["proposed_root_url"]
        if protocol_targets.get(eid) != root:
            raise AuditError("Historical protocol target differs")
        meta_raw = (historical_root / target["snapshot_metadata_path"]).read_bytes()
        csv_raw = (historical_root / target["internal_pages_path"]).read_bytes()
        if (git_blob_sha(meta_raw) != target["snapshot_metadata_git_blob_sha"]
                or git_blob_sha(csv_raw) != target["internal_pages_git_blob_sha"]):
            raise AuditError("Prior project collection source modified")
        meta = json.loads(meta_raw)
        rows = list(csv.DictReader(io.StringIO(csv_raw.decode("utf-8-sig"))))
        if (
            meta["source_url"] != root
            or meta["generated_at"] != target["snapshot_generated_at"]
            or meta["counts"]["video_links_total"] != target[
                "prior_reported_video_links_total"
            ]
            or not meta["generated_at"] < "2026-09-08"
            or not any(root in row.values() and row.get("status") == "ok"
                       for row in rows)
        ):
            raise AuditError("Prior collection root/date/record could not be proved")
    src = review["proposed_entities_scope"]["special_prior_code_for_estonia"]
    code = (historical_root / src["path"]).read_bytes()
    if (git_blob_sha(code) != src["git_blob_sha"]
            or b'ESTONIAN_FILM_ARCHIVE_PLATFORM_LABEL = "Arkaader"' not in code):
        raise AuditError("Prior Arkaader-specific implementation not verified")
    report["mode"] = "pinned_historical_sources_reverified"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--structure-only", action="store_true")
    parser.add_argument("--historical-root", type=Path)
    args = parser.parse_args()
    if (not args.structure_only) == (args.historical_root is None):
        parser.error("Specify exactly one mode: --structure-only or --historical-root")
    review = load_json(BASE / REVIEW_FILE)
    path = BASE / INVENTORY_FILE
    raw = path.read_bytes()
    inv = json.loads(raw)
    try:
        result = (
            validate_methodology_structure(review, inv, raw)
            if args.structure_only else
            verify_at_historical_commit(review, inv, raw, args.historical_root)
        )
    except (AuditError, KeyError, ValueError, OSError) as exc:
        parser.exit(1, f"VAL-009 methodology HOLD (invalid documentary source): {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
