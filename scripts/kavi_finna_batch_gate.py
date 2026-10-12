"""Bounded Finna staging with offline replay and safe cursor resume gates.

This module is an orchestration layer over the existing staging executor;
it neither downloads media nor promotes records into the MAR corpus.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from memoria_audiovisual.metadata_staging import (
    MetadataPageSource, StageRejected, public_stage_summary, stage_metadata,
)
from scripts.audit_kavi_finna_staging import audit_finna_staging

SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")


def verify_resume_expiration(
    directory: str | Path,
    *,
    now: datetime | None = None,
    safety_margin_seconds: float = 30.0,
    expected_token: str | None = None,
) -> datetime | None:
    """Check the *source-provided* expiration of a checkpoint's next cursor.

    Returns None for a completed checkpoint (no cursor). Missing/unrecognised
    expiration is a HOLD, not permission to try an unbounded continuation.
    Raw cursor values must never escape this function or its error messages.
    """
    if not 0 <= safety_margin_seconds <= 3600:
        raise ValueError("invalid_cursor_expiry_margin")
    if now is None:
        now = datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("cursor_clock_must_be_timezone_aware")
    root = Path(directory)
    try:
        checkpoint = json.loads((root / "checkpoint.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StageRejected("resume_checkpoint_unreadable") from exc
    if not isinstance(checkpoint, dict):
        raise StageRejected("resume_checkpoint_invalid")
    if checkpoint.get("status") == "complete":
        return None
    if checkpoint.get("status") != "partial":
        raise StageRejected("resume_checkpoint_not_partial")
    pages = checkpoint.get("pages")
    if not isinstance(pages, list) or not pages:
        raise StageRejected("resume_pages_missing")
    artifact_digest = pages[-1].get("artifact_sha256") if isinstance(pages[-1], dict) else None
    if not isinstance(artifact_digest, str) or not SHA256_HEX.fullmatch(artifact_digest):
        raise StageRejected("resume_invalid_artifact_sha256")
    artifact_path = root / "raw" / artifact_digest[:2] / (artifact_digest + ".json")
    try:
        raw_bytes = artifact_path.read_bytes()
    except OSError as exc:
        raise StageRejected("resume_raw_artifact_missing") from exc
    if hashlib.sha256(raw_bytes).hexdigest() != artifact_digest:
        raise StageRejected("resume_raw_artifact_tampered")
    try:
        page = json.loads(raw_bytes)["page"]
        source_cursor = page["source_response"]["resumptionToken"]
        normalized_cursor = page["next_token"]
    except (ValueError, TypeError, KeyError) as exc:
        raise StageRejected("resume_source_cursor_unverifiable") from exc
    if (
        not isinstance(source_cursor, dict)
        or not isinstance(normalized_cursor, str)
        or not normalized_cursor
        or source_cursor.get("token") != normalized_cursor
        or (expected_token is not None and normalized_cursor != expected_token)
    ):
        raise StageRejected("resume_source_cursor_mismatch")
    expires = source_cursor.get("expires")
    if not isinstance(expires, str) or not expires.strip():
        raise StageRejected("resume_cursor_expiration_missing")
    try:
        expiry = datetime.fromisoformat(expires.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StageRejected("resume_cursor_expiration_invalid") from exc
    if expiry.tzinfo is None or expiry.utcoffset() is None:
        raise StageRejected("resume_cursor_expiration_timezone_missing")
    remaining = (expiry - now).total_seconds()
    if remaining <= safety_margin_seconds:
        raise StageRejected("resume_cursor_expired_or_too_close")
    return expiry


def execute_verified_batch(
    source: MetadataPageSource,
    directory: str | Path,
    *,
    max_pages: int = 1,
    resume: bool = False,
    expected_total: int | None = None,
    delay_seconds: float = 1.0,
    expiry_margin_seconds: float = 30.0,
    sleep_fn: Callable[[float], None] = time.sleep,
    now_fn: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> dict:
    """Stage an explicit batch, then independently replay all local artifacts.

    No automatic retries or epoch resets. On resume, an operator-provided
    external total is mandatory; a cursor near expiry fails *before* API I/O.
    """
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 25:
        raise ValueError("batch_pages_must_be_between_1_and_25")
    if not isinstance(delay_seconds, (float, int)) or isinstance(delay_seconds, bool) or not 0.5 <= delay_seconds <= 30:
        raise ValueError("batch_delay_must_be_between_0_5_and_30")
    if not isinstance(expiry_margin_seconds, (float, int)) or isinstance(expiry_margin_seconds, bool) or not 0 <= expiry_margin_seconds <= 3600:
        raise ValueError("invalid_cursor_expiry_margin")
    if expected_total is not None and (
        not isinstance(expected_total, int) or isinstance(expected_total, bool)
        or expected_total < 0
    ):
        raise ValueError("expected_total_must_be_nonnegative_integer")
    scope = source.scope
    if (
        not isinstance(scope, dict)
        or scope.get("institution_code") != "fiaf-kavi"
        or scope.get("building_code") != "0/KAVI/"
        or scope.get("format_code") != "0/Video/"
    ):
        raise ValueError("unapproved_finna_batch_scope")
    evidence_sha256 = scope.get("evidence_sha256")
    if not isinstance(evidence_sha256, str) or not SHA256_HEX.fullmatch(evidence_sha256):
        raise ValueError("invalid_scope_evidence_sha256")
    if resume:
        if expected_total is None:
            raise ValueError("external_expected_total_required_on_resume")
        before = audit_finna_staging(
            directory, evidence_sha256=evidence_sha256,
            expected_total=expected_total,
        )
        if before["status"] == "complete":
            return before
        verify_resume_expiration(
            directory, now=now_fn(),
            safety_margin_seconds=expiry_margin_seconds,
        )
        # stage_metadata() only delays after the first page *within a call*.
        # Retained explicitly for the first page of every resume invocation.
        sleep_fn(delay_seconds)
    staged = stage_metadata(
        source, directory, max_pages=max_pages, resume=resume,
        request_delay_seconds=delay_seconds, sleep_fn=sleep_fn,
        # Executed by the generic staging runner WITHIN FileWriteLock,
        # immediately before EVERY continuation request. This closes both
        # the inter-process resume race and the within-batch expiry gap.
        before_fetch=lambda token: verify_resume_expiration(
            directory, expected_token=token, now=now_fn(),
            safety_margin_seconds=expiry_margin_seconds,
        ),
    )
    if expected_total is not None and staged["expected_total"] != expected_total:
        raise StageRejected("batch_expected_total_mismatch")
    audit = audit_finna_staging(
        directory, evidence_sha256=evidence_sha256,
        expected_total=staged["expected_total"],
    )
    if audit["record_count"] != public_stage_summary(staged)["record_count"]:
        raise StageRejected("batch_audit_record_count_mismatch")
    return audit
