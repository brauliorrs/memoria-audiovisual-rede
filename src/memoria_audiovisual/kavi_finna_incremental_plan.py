"""Pure, offline, review-only comparison of KAVI/Finna documentary epochs.

No network requests, file writes, media, public-index promotion, deletion,
token persistence or resumption. Reuses the approved baseline catalog gate.
Provisional candidate evidence NEVER constitutes authorization to publish.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

from .kavi_finna_mar_index import INDEX_FIELDS, _safe_record_link
from .kavi_finna_public_catalog import load_published_kavi_rows
from .metadata_staging import _digest

VERSION = "kavi-finna-reconciliation-candidate-1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_EPOCH_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$")
PROOF_FIELDS = frozenset({
    "schema_version", "unit_id", "source_service", "source_scope_sha256",
    "epoch_id", "observed_on", "stage_status", "page_count",
    "record_count", "expected_total_api_index", "source_rows_sha256",
    "source_run_url", "offline_integrity_verified",
    "api_snapshot_freshness_verified", "media_downloaded",
    "promotion_authorized",
})
# Reconcile only authorized public descriptive fields, never provenance
# evidence, rights flags or streams. Changed evidence remains held for review.
COMPARE_FIELDS = (
    "video_title", "year", "authors", "genres", "subjects", "languages",
    "video_description", "source_record_url",
)


class PlanRejected(ValueError):
    """Untrusted preview or invalid epoch proposal; no publication possible."""


def candidate_rows_sha256(rows: list[dict]) -> str:
    """Canonical fingerprint of an ordered staged preview; not proof of audit."""
    if not isinstance(rows, list) or not all(
        isinstance(row, dict) for row in rows
    ):
        raise PlanRejected("candidate_rows_invalid")
    try:
        return _digest(rows)
    except (ValueError, TypeError) as ex:
        raise PlanRejected("candidate_rows_not_serializable") from ex


def _is_iso_day(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return date.fromisoformat(value).isoformat() == value
    except ValueError:
        return False


def _validate_evidence(
    proof: dict[str, Any], rows: list[dict],
    baseline_manifest: dict[str, Any],
) -> None:
    if not isinstance(proof, dict) or set(proof) != PROOF_FIELDS:
        raise PlanRejected("candidate_evidence_fields_invalid")
    if (
        proof["schema_version"] != VERSION
        or proof["unit_id"] != "fiaf-kavi"
        or proof["source_service"] != "finna_api"
        or proof["source_scope_sha256"] != baseline_manifest["source_scope_sha256"]
        or not isinstance(proof["epoch_id"], str)
        or not SAFE_EPOCH_ID.fullmatch(proof["epoch_id"])
        or not _is_iso_day(proof["observed_on"])
        or proof["observed_on"] < baseline_manifest["observed_on"]
        or proof["stage_status"] not in ("partial", "complete")
        or proof["offline_integrity_verified"] is not True
        or proof["api_snapshot_freshness_verified"] is not False
        or proof["media_downloaded"] is not False
        or proof["promotion_authorized"] is not False
    ):
        raise PlanRejected("candidate_evidence_contract_invalid")
    page_count = proof["page_count"]
    total = proof["expected_total_api_index"]
    count = proof["record_count"]
    if (
        not isinstance(page_count, int) or isinstance(page_count, bool)
        or not 1 <= page_count <= 25
        or not isinstance(total, int) or isinstance(total, bool) or total < 1
        or not isinstance(count, int) or isinstance(count, bool)
        or not 0 < count <= total
        or count != len(rows)
        or count > page_count * 200
        or (proof["stage_status"] == "partial" and count >= total)
        or (proof["stage_status"] == "complete" and count != total)
    ):
        raise PlanRejected("candidate_pagination_counts_invalid")
    digest = proof["source_rows_sha256"]
    if (
        not isinstance(digest, str) or not SHA256.fullmatch(digest)
        or candidate_rows_sha256(rows) != digest
    ):
        raise PlanRejected("candidate_digest_mismatch")
    run_url = proof["source_run_url"]
    if (
        not isinstance(run_url, str)
        or not run_url.startswith(
            "https://github.com/brauliorrs/memoria-audiovisual-rede/actions/runs/"
        )
        or not run_url.rsplit("/", 1)[-1].isdigit()
    ):
        raise PlanRejected("candidate_evidence_run_unverifiable")


def _validate_rows(rows: list[dict], expected_scope: str) -> None:
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != set(INDEX_FIELDS):
            raise PlanRejected("candidate_unprojected_or_private_fields")
        identity = row.get("source_record_id")
        if (
            not isinstance(identity, str)
            or not identity.strip() or identity != identity.strip()
            or identity in seen
            or row.get("corpus") != "fiaf-kavi"
            or row.get("source_service") != "finna_api"
            or row.get("metadata_provider") != "0/KAVI/"
            or row.get("metadata_license") != "CC0-1.0_API_metadata_only"
            or row.get("scope_sha256") != expected_scope
            or row.get("media_access_status") != "unverified"
            or row.get("media_rights_status") != "not_verified"
            or row.get("custody_status") != "not_established"
            or row.get("record_review_status") != "unreviewed"
            or row.get("film_semantics") not in (
                "film_candidate", "unverified_audiovisual_record"
            )
            or row.get("film_semantics") != (
                "film_candidate"
                if identity.startswith("kavi.elonet_elokuva_")
                else "unverified_audiovisual_record"
            )
            or row.get("institution") != "Kuvi (KAVI historical provider)"
            or row.get("country") != "Finland"
            or row.get("continent") != "Europe"
            or row.get("platform") != "Finna / Elonet"
            or row.get("custodian") != "unknown"
            or row.get("format") != "0/Video/"
            or row.get("rights_status") != "media_rights_unverified"
            or row.get("video_subject") != row.get("subjects")
            or row.get("video_published_at") != row.get("year")
            or row.get("online_url_metadata_present") not in (
                True, False, "True", "False"
            )
            or not isinstance(row.get("video_title"), str)
            or not row["video_title"].strip()
        ):
            raise PlanRejected("candidate_row_contract_invalid")
        url = row.get("source_record_url")
        status = row.get("link_status")
        if status == "item_link_verified_by_source":
            if (
                not isinstance(url, str) or not url
                or row.get("video_link") != url
                or row.get("partner_site") != url
                or _safe_record_link(url, identity) != url
            ):
                raise PlanRejected("candidate_record_link_invalid")
        elif status == "missing_source_item_link":
            if url or row.get("video_link") or row.get("partner_site"):
                raise PlanRejected("candidate_missing_link_inconsistent")
        else:
            raise PlanRejected("candidate_link_status_invalid")
        seen.add(identity)


def plan_incremental_proposal(
    published_dir: str | Path,
    candidate_rows: list[dict],
    candidate_evidence: dict[str, Any],
) -> dict:
    """Review-only delta: new/changed/unchanged/unseen, NEVER 'deleted'.

    The baseline is independently verified against its published hash. The
    candidate digest protects consistency of input bytes across comparisons;
    a caller-set audit flag is a CLAIM and cannot certify independent replay.
    Result is exclusively a HOLD proposal, including when status=complete.
    """
    baseline_rows, baseline_manifest = load_published_kavi_rows(published_dir)
    if not baseline_rows:
        raise PlanRejected("published_baseline_missing")
    if not isinstance(candidate_rows, list) or not candidate_rows:
        raise PlanRejected("candidate_rows_empty")
    _validate_evidence(candidate_evidence, candidate_rows, baseline_manifest)
    _validate_rows(candidate_rows, baseline_manifest["source_scope_sha256"])
    baseline_by_id = {row["source_record_id"]: row for row in baseline_rows}
    proposed: list[dict] = []
    added = changed = unchanged = held_missing_links = 0
    observed: set[str] = set()
    for row in sorted(candidate_rows, key=lambda r: r["source_record_id"]):
        identity = row["source_record_id"]
        observed.add(identity)
        if row["link_status"] == "missing_source_item_link":
            held_missing_links += 1
            status = "held_missing_link"
            fields: list[str] = []
        elif identity not in baseline_by_id:
            added += 1
            status = "new"
            fields = []
        else:
            before = baseline_by_id[identity]
            fields = [
                field for field in COMPARE_FIELDS
                if str(before.get(field) or "") != str(row.get(field) or "")
            ]
            status = "changed" if fields else "unchanged"
            if fields:
                changed += 1
            else:
                unchanged += 1
        proposed.append({
            "source_record_id": identity,
            "change": status,
            "changed_fields": fields,
        })
    unseen = len(set(baseline_by_id) - observed)
    return {
        "schema_version": VERSION,
        "source_unit_id": "fiaf-kavi",
        "status": "HOLD_FOR_REVIEW",
        "evidence_status": "caller_claim_requires_independent_audit",
        "candidate_epoch_id": candidate_evidence["epoch_id"],
        "baseline_observed_on": baseline_manifest["observed_on"],
        "candidate_observed_on": candidate_evidence["observed_on"],
        "candidate_stage_status": candidate_evidence["stage_status"],
        "baseline_catalog_sha256": baseline_manifest["catalog_sha256"],
        "candidate_rows_sha256": candidate_evidence["source_rows_sha256"],
        "baseline_record_count": len(baseline_rows),
        "candidate_record_count": len(candidate_rows),
        "baseline_api_reference_total": baseline_manifest["expected_total_api_index"],
        "candidate_api_reference_total": candidate_evidence["expected_total_api_index"],
        "population_reference_changed": (
            baseline_manifest["expected_total_api_index"]
            != candidate_evidence["expected_total_api_index"]
        ),
        "added": added,
        "changed": changed,
        "unchanged": unchanged,
        "held_missing_links": held_missing_links,
        "not_observed": unseen,
        "deletion_candidates": 0,
        "snapshot_freshness_verified": False,
        "publication_authorized": False,
        "deletion_authorized": False,
        "media_downloaded": False,
        "corpus_activation": False,
        "deltas": proposed,
    }
