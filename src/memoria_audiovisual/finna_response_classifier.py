"""Conservative Finna REST API failure classification — no expiration inference.

This module classifies safe structural evidence only. No documented machine
signature for an expired Finna REST search resumptionToken is currently pinned,
so EVERY classification keeps expiration and restart authorization false.

A future verified signature must be approved separately, never inferred from
HTTP 400/404, a free-text message, the client's clock or a transport error.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FailureAssessment:
    category: str
    reason: str
    manual_retry_candidate: bool = False
    token_expiration_confirmed: bool = False
    restart_authorized: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "failure_category": self.category,
            "reason": self.reason,
            "manual_retry_candidate": self.manual_retry_candidate,
            "token_expiration_confirmed": False,
            "restart_authorized": False,
            "promotion_authorized": False,
            "media_downloaded": False,
        }


def _failure(
    category: str, reason: str, *, manual_retry_candidate: bool = False,
) -> FailureAssessment:
    return FailureAssessment(category, reason, manual_retry_candidate)


def classify_http_status(status: object) -> FailureAssessment | None:
    """Interpret HTTP semantics, not text in an error page/JSON body."""
    if status == 200 and type(status) is int:
        return None
    if type(status) is not int or status < 100 or status > 599:
        return _failure("unknown_http_status", "finna_http_status_unknown")
    reason = f"finna_http_status_{status}"
    if status == 429:
        return _failure("rate_limited", reason, manual_retry_candidate=True)
    if status == 403:
        return _failure("access_denied", reason)
    if status in (408, 425):
        return _failure("http_timeout_or_too_early", reason, manual_retry_candidate=True)
    if status >= 500:
        return _failure("upstream_failure", reason, manual_retry_candidate=True)
    if status >= 400:
        return _failure("client_error_unverified", reason)
    if status >= 300:
        return _failure("unexpected_redirect", reason)
    return _failure("unexpected_http_status", reason)


def classify_api_payload(payload: object) -> FailureAssessment | None:
    """Only status OK/ok is accepted; even 'expired' text is untrusted."""
    if isinstance(payload, dict) and payload.get("status") in ("OK", "ok"):
        return None
    return _failure("api_rejection_unverified", "finna_api_status_invalid")


_HTTP_REASON = re.compile(r"^finna_http_status_([1-5][0-9]{2})$")

# Stable codes from our own checked adapter, not provider messages.
_SNAPSHOT = frozenset({
    "checkpoint_total_drift",
    "result_total_drift",
    "terminal_total_mismatch",
    "records_exceed_preflight_total",
})
_ACCESS = frozenset({
    "finna_robots_or_origin_block",
    "finna_guard_redirect_outside_https_scope",
    "finna_guard_redirect_cycle",
    "finna_guard_redirect_budget_exceeded",
})
_TRANSPORT = frozenset({
    "finna_guard_transport_unverifiable",
    "finna_guard_stream_read_failed",
    "finna_guard_body_size_limit",
    "finna_unexpected_content_type",
    "finna_invalid_json",
})
_SOURCE_SHAPE = frozenset({
    "finna_api_status_invalid",
    "finna_invalid_result_count",
    "finna_count_response_not_empty",
    "finna_records_not_list",
    "resumption_token_object_missing_token",
    "invalid_resumption_token_object",
    "invalid_resumption_token_value",
    "finna_count_response_not_empty",
})
_LOCAL_EXPIRY_AMBIGUOUS = frozenset({
    "resume_cursor_expiration_timezone_missing",
    "resume_cursor_expiration_missing",
    "resume_cursor_expiration_invalid",
    "resume_cursor_expired_or_too_close",
    "resume_source_cursor_mismatch",
})
_INTEGRITY = frozenset({
    "checkpoint_cursor_chain_mismatch",
    "checkpoint_raw_artifact_tampered",
    "checkpoint_duplicate_cross_page",
    "duplicate_ids_across_pages",
    "duplicate_ids_within_page",
    "checkpoint_scope_mismatch",
    "checkpoint_page_next_cursor_hash_mismatch",
    "checkpoint_promotion_gate_tampered",
    "checkpoint_media_download_gate_tampered",
    "staging_epoch_aborted",
})


def classify_stage_rejection(code: object) -> FailureAssessment:
    """Map locally controlled error codes to a redacted operational category.

    Never publish a raw, unrecognized StageRejected string: it may contain
    an opaque cursor, record ID or URL embedded by an upstream exception.
    """
    if not isinstance(code, str):
        return _failure("unknown_rejection", "finna_unclassified_failure")
    matched = _HTTP_REASON.fullmatch(code)
    if matched:
        return classify_http_status(int(matched.group(1))) or _failure(
            "unknown_rejection", "finna_unclassified_failure"
        )
    if code == "finna_http_status_unknown":
        return _failure("unknown_http_status", code)
    if code in _SNAPSHOT:
        return _failure("snapshot_drift", code)
    if code in _ACCESS:
        return _failure("access_denied", code)
    if code in _TRANSPORT:
        return _failure("transport_or_response_unverifiable", code)
    if code in _SOURCE_SHAPE:
        return _failure("api_rejection_or_shape_unverified", code)
    if code in _LOCAL_EXPIRY_AMBIGUOUS:
        return _failure("local_expiry_unverified", code)
    if code in _INTEGRITY:
        return _failure("integrity_failure", code)
    return _failure("unknown_rejection", "finna_unclassified_failure")
