"""Offline hypotheses for timezone-naive Finna expiration timestamps.

This is *diagnostic only*. It never contacts the API and must not be used as
proof of the server's timezone or to trigger automatic corpus restarts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HELSINKI = ZoneInfo("Europe/Helsinki")


@dataclass(frozen=True)
class ExpiryHypotheses:
    """Public categorical evidence; opaque cursors are never an input."""

    classification: str
    utc_candidate: datetime
    helsinki_candidate: datetime | None
    utc_offset_hours: float | None
    # This is not a source-validated expiration or authorization to fetch.


def assess_naive_finna_expiry(
    expires: str,
    *,
    now: datetime,
    safety_margin_seconds: float = 30.0,
) -> ExpiryHypotheses:
    """Compare UTC and Europe/Helsinki assumptions without endorsing either.

    both_future / both_past / disagreement require the clock candidates to
    be unambiguous. DST overlap/gaps are classified separately. This function
    changes no live request or existing strict expiration gate.
    """
    if not isinstance(expires, str) or not expires.strip():
        raise ValueError("expires_required")
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("aware_now_required")
    if (
        isinstance(safety_margin_seconds, bool)
        or not isinstance(safety_margin_seconds, (int, float))
        or not 0 <= safety_margin_seconds <= 3600
    ):
        raise ValueError("invalid_margin")
    try:
        instant = datetime.fromisoformat(expires)
    except ValueError as exc:
        raise ValueError("invalid_expiry_datetime") from exc
    if instant.tzinfo is not None:
        raise ValueError("requires_naive_expiry")
    utc_candidate = instant.replace(tzinfo=timezone.utc)
    # Roundtrip detects imaginary spring-forward local times and ambiguous
    # autumn fold; neither may silently be resolved by the machine timezone.
    valid_local: set[datetime] = set()
    local_offsets: set[timedelta] = set()
    for fold in (0, 1):
        local = instant.replace(tzinfo=HELSINKI, fold=fold)
        candidate = local.astimezone(timezone.utc)
        restored = candidate.astimezone(HELSINKI).replace(tzinfo=None)
        if restored == instant:
            valid_local.add(candidate)
            local_offsets.add(local.utcoffset())
    if len(valid_local) != 1:
        classification = (
            "helsinki_nonexistent_time" if not valid_local
            else "helsinki_dst_fold_ambiguous"
        )
        return ExpiryHypotheses(classification, utc_candidate, None, None)
    local_candidate = next(iter(valid_local))
    margin = now.astimezone(timezone.utc) + timedelta(seconds=safety_margin_seconds)
    if utc_candidate > margin and local_candidate > margin:
        classification = "both_future"
    elif utc_candidate <= margin and local_candidate <= margin:
        classification = "both_past"
    else:
        classification = "disagreement"
    offset_hours = next(iter(local_offsets)).total_seconds() / 3600
    return ExpiryHypotheses(
        classification, utc_candidate, local_candidate, offset_hours
    )
