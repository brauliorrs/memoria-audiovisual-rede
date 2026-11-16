"""Produce a review-only, auditable proposal compatible with PR #95's field layout.

Consumes the SHA-pinned local evidence through PR #96's parser. Does NOT
promote, publish or approve metadata, and never contacts an upstream server.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from memoria_audiovisual.eye_czech_reconciliation import (
    ReconciliationRejected, _normalize_record, _fingerprint,
)
from scripts.preview_eye_czech_reconciliation import preview, DEFAULT_EYE_CSV, MAX_JSON

# PR #95 contract. Keep in sync, but never set publication-approved status here.
ADMISSION_FIELDS = (
    "source_record_id", "source_record_url", "video_title", "year",
    "authors", "subjects", "languages", "genres", "video_description",
    "media_access_status", "media_rights_status", "record_review_status",
)
PENDING_REVIEW = "pending_independent_review"


def _read_json(evidence_file: Path, expected_sha: str, corpus: str) -> dict:
    if not evidence_file.is_file() or evidence_file.is_symlink():
        raise ReconciliationRejected("missing_or_symlinked_evidence")
    if evidence_file.stat().st_size > MAX_JSON:
        raise ReconciliationRejected("oversized_evidence")
    raw = evidence_file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ReconciliationRejected("evidence_sha256_mismatch")
    try:
        payload = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ReconciliationRejected("evidence_json_invalid") from exc
    if not isinstance(payload, dict) or payload.get("corpus") != corpus:
        raise ReconciliationRejected("evidence_scope_mismatch")
    return payload


def _as_pending_row(source: dict, corpus: str) -> dict:
    normalized = _normalize_record(source, corpus=corpus)
    rid = source.get("record_id")
    if not isinstance(rid, str) or not rid or len(rid) > 220:
        raise ReconciliationRejected("candidate_record_id_missing")
    title = normalized["title"]
    if len(title) > 600:
        raise ReconciliationRejected("candidate_title_too_long")
    # No inference of license, ownership, streaming, authors or languages.
    row = {
        "source_record_id": rid,
        "source_record_url": normalized["origin_url"],
        "video_title": title,
        "year": normalized["date"],
        "authors": "",
        "subjects": normalized["subject"],
        "languages": "",
        "genres": "",
        "video_description": normalized["description"],
        "media_access_status": "unverified",
        "media_rights_status": "not_verified",
        "record_review_status": PENDING_REVIEW,
    }
    if any(len(value) > 2000 for value in row.values()):
        raise ReconciliationRejected("candidate_field_too_long")
    return row


def build_review_proposal(
    corpus: str, evidence_file: Path, expected_sha: str,
    *, eye_catalog: Path = DEFAULT_EYE_CSV,
) -> tuple[bytes, dict]:
    """Compute deltas from the original evidence, not a user-authored report."""
    if corpus not in ("eye", "czech"):
        raise ReconciliationRejected("unsupported_corpus")
    source = _read_json(evidence_file, expected_sha, corpus)
    assessment = preview(corpus, evidence_file, expected_sha, eye_catalog=eye_catalog)
    candidates = []
    omitted_updates = []
    if corpus == "eye":
        original = source.get("records")
        if not isinstance(original, list):
            raise ReconciliationRejected("eye_records_not_list")
        by_url = {}
        for item in original:
            normalized = _normalize_record(item, corpus="eye")
            url = normalized["origin_url"]
            if url in by_url:
                raise ReconciliationRejected("duplicate_candidate_url")
            by_url[url] = item
        for change in assessment["changes"]:
            if change["status"] == "changed":
                omitted_updates.append(change["origin_url"])
                continue
            if change["status"] != "new":
                continue
            item = by_url.get(change["origin_url"])
            if item is None or _fingerprint(_normalize_record(item, corpus="eye")) != change["metadata_sha256"]:
                raise ReconciliationRejected("reconciliation_fingerprint_disagrees")
            candidates.append(_as_pending_row(item, corpus="eye"))
        # unchanged and not_observed never enter a new-admission CSV.
    else:
        if assessment.get("status") == "candidate_for_review":
            source_row = source.get("episode")
            if not isinstance(source_row, dict):
                raise ReconciliationRejected("czech_episode_missing")
            normalized = _normalize_record(source_row, corpus="czech")
            if (_fingerprint(normalized) != assessment["metadata_sha256"]
                    or normalized["origin_url"] != assessment["origin_url"]):
                raise ReconciliationRejected("czech_provenance_mismatch")
            candidates = [_as_pending_row(source_row, corpus="czech")]
        elif assessment.get("status") != "HOLD":
            raise ReconciliationRejected("unexpected_czech_state")
    candidates.sort(key=lambda x: (x["source_record_url"], x["source_record_id"]))
    # CSV with pending status MUST fail PR #95 admission (approved_metadata_only).
    text_output = io.StringIO(newline="")
    writer = csv.DictWriter(text_output, fieldnames=ADMISSION_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(candidates)
    csv_data = text_output.getvalue().encode("utf-8")
    manifest = {
        "schema_version": "mar-review-proposal-v1",
        "corpus": "eye" if corpus == "eye" else "czech-television",
        "status": "pending_independent_review" if candidates else "HOLD_no_new_admission",
        "evidence_sha256": expected_sha,
        "candidate_csv_sha256": hashlib.sha256(csv_data).hexdigest(),
        "candidate_count": len(candidates),
        "legacy_updates_requiring_separate_review": len(omitted_updates),
        "legacy_updates_urls": omitted_updates,
        "not_observed_is_not_deletion": True,
        "publication_authorized": False,
        "media_downloaded": False,
        "corpus_activation": False,
        "production_gate": "HOLD",
        "next_gate": "independent_curatorial_review_and_PR95_manifest",
    }
    return csv_data, manifest


def write_review_proposal(
    corpus: str, evidence_file: Path, expected_sha: str, output_dir: Path,
    *, eye_catalog: Path = DEFAULT_EYE_CSV,
) -> dict:
    """Only write to a NEW explicit review directory outside active MAR data."""
    active_data = (Path(__file__).resolve().parents[1] / "data").resolve()
    output = output_dir.resolve()
    if output == active_data or active_data in output.parents:
        raise ReconciliationRejected("cannot_write_to_active_catalog")
    if output.exists() or output.is_symlink():
        raise ReconciliationRejected("review_output_must_not_preexist")
    csv_bytes, proposal = build_review_proposal(
        corpus, evidence_file, expected_sha, eye_catalog=eye_catalog,
    )
    # Avoid partial output with fake approval; only write reviewed candidate files.
    output.mkdir(parents=True, exist_ok=False)
    try:
        name = "eye" if corpus == "eye" else "czech-television"
        (output / f"{name}.candidate.csv").write_bytes(csv_bytes)
        (output / f"{name}.proposal.json").write_text(
            json.dumps(proposal, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # Preserve files for forensic investigation; caller reports error.
        raise
    return proposal


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", choices=["eye", "czech"])
    parser.add_argument("--evidence-file", type=Path, required=True)
    parser.add_argument("--evidence-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--eye-catalog", type=Path, default=DEFAULT_EYE_CSV)
    args = parser.parse_args(argv)
    try:
        result = write_review_proposal(
            args.corpus, args.evidence_file, args.evidence_sha256,
            args.output_dir, eye_catalog=args.eye_catalog,
        )
    except (ReconciliationRejected, OSError, TypeError, ValueError):
        print(json.dumps({
            "status": "HOLD", "publication_authorized": False,
            "production_gate": "HOLD",
        }))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
