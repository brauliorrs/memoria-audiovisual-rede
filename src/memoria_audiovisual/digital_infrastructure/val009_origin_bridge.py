"""VAL-009 origin capture bridge: bounded offline-testable HTTP and v23 events.

Neither path creates a scientific freeze, generates predictions, or authorizes
independent collection. The caller must supply a preapproved bounded traversal,
robots evidence, a frozen scope policy and a clock with a real timezone.
Legacy derived page reports WITHOUT origin captures are rejected.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

import requests

from .val009_capture_provenance import (
    CapturedPage,
    CaptureProvenanceError,
    url_identity,
)

_ALLOWED_MEDIA = (
    "text/html", "application/xhtml+xml", "application/json",
    "application/ld+json", "text/plain",
)
_LEGACY_STATES = frozenset({
    "fetched", "blocked_by_robots", "request_error", "http_error",
    "unsupported_content_type", "redirect_outside_scope",
})


@dataclass(frozen=True)
class OriginSpec:
    entity_id: str
    root_url: str
    requested_url: str
    discovery_index: int
    parent_url: str | None = None
    depth: int = 0
    collector_protocol_version: str = "2.3.0-dev"


def _checked(spec: OriginSpec) -> None:
    if (
        not isinstance(spec.entity_id, str) or not spec.entity_id.strip()
        or type(spec.discovery_index) is not int or spec.discovery_index < 0
        or type(spec.depth) is not int or spec.depth < 0
        or not isinstance(spec.collector_protocol_version, str)
        or not spec.collector_protocol_version.strip()
    ):
        raise CaptureProvenanceError("Missing/invalid original traversal identity")
    for value in (spec.root_url, spec.requested_url):
        url_identity(value)
    if spec.parent_url is not None:
        url_identity(spec.parent_url)


def _decision(value: tuple[bool, Mapping[str, Any]]) -> dict[str, Any]:
    if (
        not isinstance(value, tuple) or len(value) != 2
        or type(value[0]) is not bool or not isinstance(value[1], Mapping)
    ):
        raise CaptureProvenanceError("Missing/ambiguous robots decision")
    evidence = dict(value[1])
    if (
        evidence.get("checked") is not True
        or type(evidence.get("allowed")) is not bool
        or evidence["allowed"] is not value[0]
        or not isinstance(evidence.get("reason"), str)
        or not evidence["reason"].strip()
    ):
        raise CaptureProvenanceError("Incomplete robots evidence")
    return evidence


def _status(*, final_url: str, status: int, media_type: str,
            root_url: str, is_in_scope: Callable[[str, str], bool]) -> str:
    # Preserve old v23 precedence: out-of-scope redirect, HTTP error, media.
    if not is_in_scope(final_url, root_url):
        return "redirect_outside_scope"
    if status >= 400:
        return "http_error"
    if not any(media_type.startswith(prefix) for prefix in _ALLOWED_MEDIA):
        return "unsupported_content_type"
    return "fetched"


def capture_origin_http(
    spec: OriginSpec, *, get: Callable[..., Any],
    robots_decision: Callable[[str], tuple[bool, Mapping[str, Any]]],
    is_in_scope: Callable[[str, str], bool],
    clock: Callable[[], str],
    max_response_bytes: int = 1_500_000,
    timeout_seconds: float = 12.0,
) -> CapturedPage:
    """Capture an already-scheduled request BEFORE classifier-page reduction.

    get must support stream=True and return a response with .url, .status_code,
    .headers and .iter_content(). Cap+1 proves truncation but is NOT the
    total server response length: response_received_bytes is observed bytes.
    """
    _checked(spec)
    if type(max_response_bytes) is not int or max_response_bytes <= 0:
        raise CaptureProvenanceError("Invalid capture byte limit")
    if (not isinstance(timeout_seconds, (int, float))
            or isinstance(timeout_seconds, bool) or timeout_seconds <= 0):
        raise CaptureProvenanceError("Invalid request timeout")
    evidence = _decision(robots_decision(spec.requested_url))
    common = dict(
        entity_id=spec.entity_id, root_url=spec.root_url,
        requested_url=spec.requested_url, discovery_index=spec.discovery_index,
        robots_evidence=evidence, parent_url=spec.parent_url, depth=spec.depth,
        collector_protocol_version=spec.collector_protocol_version,
    )
    if evidence["allowed"] is False:
        result = CapturedPage(
            **common, final_url=None, captured_at=clock(),
            capture_state="blocked_by_robots", raw_body=b"",
            response_received_bytes=0,
        )
        result.validate()
        return result
    response = None
    try:
        response = get(
            spec.requested_url, timeout=timeout_seconds,
            allow_redirects=True, stream=True,
        )
    except requests.RequestException as exc:
        result = CapturedPage(
            **common, final_url=None, captured_at=clock(),
            capture_state="request_error", raw_body=b"",
            response_received_bytes=0, error_type=type(exc).__name__,
            error_message=str(exc),
        )
        result.validate()
        return result
    try:
        final_url = getattr(response, "url", None)
        status = getattr(response, "status_code", None)
        if (not isinstance(final_url, str) or type(status) is not int
                or not 100 <= status <= 599):
            raise CaptureProvenanceError(
                "Origin response lacks an explicit final URL/HTTP status"
            )
        url_identity(final_url)  # No silent fallback to requested URL.
        headers = getattr(response, "headers", None)
        if not isinstance(headers, Mapping):
            raise CaptureProvenanceError("Origin response lacks headers")
        media_type = str(headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if not callable(getattr(response, "iter_content", None)):
            raise CaptureProvenanceError("Origin response lacks bounded byte stream")
        parts: list[bytes] = []
        observed = 0
        try:
            chunks: Iterable[bytes] = response.iter_content(
                chunk_size=min(max_response_bytes + 1, 8192)
            )
            for chunk in chunks:
                if not isinstance(chunk, bytes):
                    raise CaptureProvenanceError("Non-byte HTTP response fragment")
                if not chunk:
                    continue
                remaining = max_response_bytes - sum(len(part) for part in parts)
                if remaining > 0:
                    parts.append(chunk[:remaining])
                observed += len(chunk)
                if observed > max_response_bytes:
                    break
        except requests.RequestException as exc:
            raise CaptureProvenanceError(
                "Interrupted response stream; no complete capture event"
            ) from exc
        raw_body = b"".join(parts)
        truncated = observed > max_response_bytes
        result = CapturedPage(
            **common, final_url=final_url, captured_at=clock(),
            capture_state=_status(
                final_url=final_url, status=status, media_type=media_type,
                root_url=spec.root_url, is_in_scope=is_in_scope,
            ), raw_body=raw_body, http_status_code=status,
            media_type=media_type or None, response_received_bytes=observed,
            response_truncated=truncated,
        )
        result.validate()
        return result
    finally:
        close = getattr(response, "close", None)
        if callable(close):
            close()


def from_v23_origin_report(report: Any, *, entity_id: str) -> tuple[CapturedPage, ...]:
    """Translate historical v23 origin events; REFUSE derived-only reports.

    This bridge does not run the old 968-line collector, does not call its
    classifier and does not derive missing origin fields from SurfacePage.url.
    The capture and derived page must have matching state, time and body hash.
    """
    captures = getattr(report, "captures", None)
    pages = getattr(report, "pages", None)
    root_url = getattr(report, "root_url", None)
    protocol_version = getattr(report, "protocol_version", None)
    if (
        not isinstance(captures, (list, tuple))
        or not captures
        or not isinstance(pages, (list, tuple))
        or len(captures) != len(pages)
        or not isinstance(protocol_version, str) or not protocol_version
    ):
        raise CaptureProvenanceError("Missing v23 original capture event(s)")
    url_identity(root_url)
    results: list[CapturedPage] = []
    for index, (origin, page) in enumerate(zip(captures, pages)):
        state = getattr(origin, "fetch_status", None)
        if state not in _LEGACY_STATES:
            raise CaptureProvenanceError("Unsupported/missing v23 origin state")
        if (getattr(page, "fetch_status", None) != state
                or getattr(page, "fetched_at", None) != getattr(origin, "observed_at", None)
                or getattr(page, "status_code", None) != getattr(origin, "status_code", None)):
            raise CaptureProvenanceError("Origin event and derived page disagree")
        body = getattr(origin, "response_body", None)
        if body is None:
            body = b""
        if not isinstance(body, bytes):
            raise CaptureProvenanceError("Raw origin body must be bytes")
        reported_sha = getattr(page, "content_sha256", None)
        if reported_sha is not None and reported_sha != hashlib.sha256(body).hexdigest():
            raise CaptureProvenanceError("Derived page hash differs from origin bytes")
        if body and reported_sha is None:
            raise CaptureProvenanceError("Derived page omits observed body hash")
        received = getattr(origin, "response_received_bytes", None)
        if received is None and getattr(origin, "status_code", None) is not None:
            raise CaptureProvenanceError("v23 response byte count was not preserved")
        if received is None:
            received = 0
        truncated = getattr(origin, "response_truncated", None)
        if type(truncated) is not bool:
            raise CaptureProvenanceError("Missing v23 truncation marker")
        robots = getattr(origin, "robots_evidence", None)
        if not isinstance(robots, dict) or "reason" not in robots:
            raise CaptureProvenanceError("Missing robots provenance on v23 event")
        if state == "blocked_by_robots" and robots.get("allowed") is not False:
            raise CaptureProvenanceError("Robots block lacks denial evidence")
        final = getattr(origin, "final_url", None)
        if state in {"blocked_by_robots", "request_error"} and final is not None:
            raise CaptureProvenanceError("No-response observation claims final URL")
        # SurfacePage.url canonicalizes query ordering; never overwrite
        # final_url from the original v23 capture event.
        if state in {"blocked_by_robots", "request_error"} and (
            getattr(page, "url", None) != getattr(origin, "requested_url", None)
        ):
            raise CaptureProvenanceError("No-response derived page contradicts origin")
        if final is not None and state != "redirect_outside_scope":
            from urllib.parse import urlsplit
            a = urlsplit(url_identity(getattr(page, "url", None)))
            b = urlsplit(url_identity(final))
            if (a.scheme, a.netloc, a.path) != (b.scheme, b.netloc, b.path):
                raise CaptureProvenanceError("Derived page route contradicts origin")
        result = CapturedPage(
            entity_id=entity_id, root_url=root_url,
            requested_url=getattr(origin, "requested_url", None),
            final_url=final, discovery_index=index,
            captured_at=getattr(origin, "observed_at", None),
            capture_state=state, raw_body=body,
            http_status_code=getattr(origin, "status_code", None),
            media_type=getattr(origin, "content_type", None),
            response_received_bytes=received, response_truncated=truncated,
            robots_evidence=robots,
            error_type=getattr(origin, "error_type", None),
            error_message=getattr(origin, "error_message", None),
            parent_url=getattr(page, "parent_url", None),
            depth=getattr(page, "depth", None),
            collector_protocol_version=protocol_version,
        )
        result.validate()
        results.append(result)
    return tuple(results)
