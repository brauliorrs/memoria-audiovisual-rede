"""Offline VAL-009 collector provenance; no crawling, prediction or scientific seal.

Only accepts observations that retain requested and final URLs separately.
Stores exact nonempty response bytes; a typed JSON envelope is used only
when no response body exists, so HTTP/transport errors remain auditable.
The caller, not this module, must ensure independently authenticated seals
and durable access-controlled custody.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping
from urllib.parse import urlsplit, urlunsplit

from .locking import FileWriteLock

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_STATES = frozenset({
    "fetched", "http_error", "collector_blocked", "geo_restricted",
    "redirect_outside_scope", "request_error", "blocked_by_robots",
    "unsupported_content_type",
})
_HUMAN_FIELDS = (
    "human_surface_type", "human_is_item_level", "human_access_state",
    "human_review_note", "reviewer_id", "reviewed_at",
)


class CaptureProvenanceError(ValueError):
    """Fail closed on changed, incomplete or ambiguous capture evidence."""


def _json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _instant(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise CaptureProvenanceError("Missing timestamp")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise CaptureProvenanceError("Invalid timestamp") from exc
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        raise CaptureProvenanceError("Capture timestamps require timezone")
    return stamp


def url_identity(value: str) -> str:
    """Conservative identity: normalize authority, not path case/query order."""
    if not isinstance(value, str) or not value or any(c.isspace() for c in value):
        raise CaptureProvenanceError("Missing/invalid explicit HTTP(S) URL")
    try:
        parts = urlsplit(value)
        if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
            raise ValueError("Unsupported/missing authority")
        if parts.username is not None or parts.password is not None:
            raise ValueError("Credential-bearing URL")
        scheme, host, port = parts.scheme.lower(), parts.hostname.lower(), parts.port
        if ":" in host:
            host = f"[{host}]"
        if port is not None and (scheme, port) not in {("http", 80), ("https", 443)}:
            host += f":{port}"
        return urlunsplit((scheme, host, parts.path, parts.query, ""))
    except ValueError as exc:
        raise CaptureProvenanceError("Invalid HTTP(S) URL") from exc


@dataclass(frozen=True)
class CapturedPage:
    entity_id: str
    root_url: str
    requested_url: str
    final_url: str | None  # None means unknown; never reconstruct from a redirect.
    discovery_index: int   # Zero-based traversal position within an entity.
    captured_at: str       # Explicit timezone is mandatory.
    capture_state: str
    raw_body: bytes        # Exact source bytes, not parsed or reserialized HTML.
    http_status_code: int | None = None
    media_type: str | None = None
    response_received_bytes: int | None = None
    response_truncated: bool = False
    robots_evidence: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None
    parent_url: str | None = None
    depth: int | None = None
    collector_protocol_version: str | None = None

    def validate(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise CaptureProvenanceError("Missing entity ID")
        url_identity(self.root_url)
        url_identity(self.requested_url)
        if self.final_url is not None:
            url_identity(self.final_url)
        if type(self.discovery_index) is not int or self.discovery_index < 0:
            raise CaptureProvenanceError("Invalid discovery order")
        _instant(self.captured_at)
        if self.capture_state not in _STATES or not isinstance(self.raw_body, bytes):
            raise CaptureProvenanceError("Invalid capture state or raw bytes")
        if self.http_status_code is not None and (
            type(self.http_status_code) is not int
            or not 100 <= self.http_status_code <= 599
        ):
            raise CaptureProvenanceError("Invalid HTTP status code")
        if self.response_received_bytes is not None and (
            type(self.response_received_bytes) is not int
            or self.response_received_bytes < len(self.raw_body)
        ):
            raise CaptureProvenanceError("Invalid received byte count")
        if type(self.response_truncated) is not bool:
            raise CaptureProvenanceError("Invalid truncation marker")
        if self.response_truncated and (
            self.response_received_bytes is None
            or self.response_received_bytes <= len(self.raw_body)
        ):
            raise CaptureProvenanceError(
                "Truncated body needs explicit received byte lower bound"
            )
        if (not self.response_truncated
                and self.response_received_bytes is not None
                and self.response_received_bytes != len(self.raw_body)):
            raise CaptureProvenanceError("Untruncated body length mismatch")
        if self.robots_evidence is not None:
            if not isinstance(self.robots_evidence, dict):
                raise CaptureProvenanceError("Invalid robots evidence")
            try:
                _json(self.robots_evidence)
            except (TypeError, ValueError) as exc:
                raise CaptureProvenanceError("Non-JSON robots evidence") from exc
        if self.parent_url is not None:
            url_identity(self.parent_url)
        if self.depth is not None and (
            type(self.depth) is not int or self.depth < 0
        ):
            raise CaptureProvenanceError("Invalid collection depth")
        if self.collector_protocol_version is not None and (
            not isinstance(self.collector_protocol_version, str)
            or not self.collector_protocol_version.strip()
        ):
            raise CaptureProvenanceError("Invalid collector protocol version")
        if self.capture_state in {"blocked_by_robots", "request_error"} and (
            self.final_url is not None or self.http_status_code is not None
            or self.raw_body or self.response_truncated
        ):
            raise CaptureProvenanceError(
                "No-response capture cannot claim URL, HTTP status or response bytes"
            )
        if self.capture_state in {"unsupported_content_type", "redirect_outside_scope"}:
            if self.final_url is None or self.http_status_code is None:
                raise CaptureProvenanceError("HTTP observation missing final URL/status")
        if self.capture_state == "unsupported_content_type" and (
            self.http_status_code is None
            or not 200 <= self.http_status_code < 400
        ):
            raise CaptureProvenanceError(
                "Unsupported media is not an HTTP error"
            )
        if self.capture_state == "fetched":
            if (
                self.final_url is None
                or self.http_status_code is None
                or not 200 <= self.http_status_code < 400
            ):
                raise CaptureProvenanceError(
                    "Successful capture requires final URL, bytes and 2xx/3xx status"
                )
        if self.capture_state == "http_error":
            if (
                self.final_url is None or self.http_status_code is None
                or self.http_status_code < 400
            ):
                raise CaptureProvenanceError(
                    "HTTP error requires actual final URL and error status"
                )
        if self.media_type is not None and (
            not isinstance(self.media_type, str) or not self.media_type.strip()
        ):
            raise CaptureProvenanceError("Invalid media type")


@dataclass(frozen=True)
class Receipt:
    review_unit_id: str
    entity_id: str
    root_url: str
    requested_url: str
    final_url: str | None
    page_url: str
    discovery_index: int
    captured_at: str
    capture_state: str
    http_status_code: int | None
    media_type: str | None
    raw_body_sha256: str
    snapshot_reference: str
    snapshot_sha256: str
    payload_kind: str
    response_received_bytes: int = 0
    response_truncated: bool = False
    robots_evidence: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None
    parent_url: str | None = None
    depth: int | None = None
    collector_protocol_version: str | None = None

    def document(self) -> dict[str, Any]:
        return dict(vars(self))


class CaptureStore:
    """Immutable content-addressed local bytes and per-observation receipts.

    A path existing here is NOT an external trusted timestamp, vault or seal.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, category: str, digest: str) -> Path:
        if not _HASH.fullmatch(digest):
            raise CaptureProvenanceError("Invalid artifact digest")
        return self.root / category / digest[:2] / digest

    def _write_immutable(self, target: Path, data: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        with FileWriteLock(target):
            if target.exists():
                if target.read_bytes() != data:
                    raise CaptureProvenanceError("Existing immutable evidence changed")
                return
            temporary = target.with_name(f"{target.name}.{os.getpid()}.tmp")
            try:
                with temporary.open("xb") as handle:
                    handle.write(data)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)

    def persist(self, capture: CapturedPage) -> Receipt:
        capture.validate()
        kind = (
            "raw_response_bytes" if capture.raw_body
            else "empty_response_envelope" if capture.http_status_code is not None
            else "no_response_envelope"
        )
        material = capture.raw_body if capture.raw_body else _json({
            "artifact_kind": kind,
            "entity_id": capture.entity_id,
            "requested_url": capture.requested_url,
            "final_url": capture.final_url,
            "captured_at": capture.captured_at,
            "capture_state": capture.capture_state,
            "http_status_code": capture.http_status_code,
            "raw_body_sha256": _digest(b""),
            "discovery_index": capture.discovery_index,
        })
        material_sha = _digest(material)
        identity = _digest(_json({
            "entity_id": capture.entity_id,
            "requested_url": capture.requested_url,
            "final_url": capture.final_url,
            "discovery_index": capture.discovery_index,
        }))[:24]
        receipt = Receipt(
            review_unit_id=f"val009-{identity}",
            entity_id=capture.entity_id,
            root_url=capture.root_url,
            requested_url=capture.requested_url,
            final_url=capture.final_url,
            page_url=(capture.final_url if capture.final_url is not None
                      else capture.requested_url),
            discovery_index=capture.discovery_index,
            captured_at=capture.captured_at,
            capture_state=capture.capture_state,
            http_status_code=capture.http_status_code,
            media_type=capture.media_type,
            raw_body_sha256=_digest(capture.raw_body),
            snapshot_reference=f"snapshot/{material_sha}",
            snapshot_sha256=material_sha,
            payload_kind=kind,
            response_received_bytes=(
                capture.response_received_bytes
                if capture.response_received_bytes is not None
                else len(capture.raw_body)
            ),
            response_truncated=capture.response_truncated,
            robots_evidence=capture.robots_evidence,
            error_type=capture.error_type,
            error_message=capture.error_message,
            parent_url=capture.parent_url,
            depth=capture.depth,
            collector_protocol_version=capture.collector_protocol_version,
        )
        self._write_immutable(self._path("snapshots", material_sha), material)
        receipt_bytes = _json(receipt.document())
        self._write_immutable(
            self._path("receipts", _digest(receipt_bytes)), receipt_bytes
        )
        return receipt

    def load(self, receipt: Receipt) -> bytes:
        try:
            data = self._path("snapshots", receipt.snapshot_sha256).read_bytes()
        except OSError as exc:
            raise CaptureProvenanceError("Missing or unreadable raw snapshot") from exc
        if _digest(data) != receipt.snapshot_sha256:
            raise CaptureProvenanceError("Snapshot bytes changed")
        receipt_bytes = _json(receipt.document())
        try:
            saved = self._path("receipts", _digest(receipt_bytes)).read_bytes()
        except OSError as exc:
            raise CaptureProvenanceError("Missing or unreadable receipt") from exc
        if saved != receipt_bytes:
            raise CaptureProvenanceError("Capture receipt changed")
        if receipt.snapshot_reference != f"snapshot/{receipt.snapshot_sha256}":
            raise CaptureProvenanceError("Snapshot reference mismatch")
        if receipt.payload_kind in {"no_response_envelope", "empty_response_envelope"}:
            expected = _json({
                "artifact_kind": receipt.payload_kind,
                "entity_id": receipt.entity_id,
                "requested_url": receipt.requested_url,
                "final_url": receipt.final_url,
                "captured_at": receipt.captured_at,
                "capture_state": receipt.capture_state,
                "http_status_code": receipt.http_status_code,
                "raw_body_sha256": _digest(b""),
                "discovery_index": receipt.discovery_index,
            })
            if data != expected or receipt.raw_body_sha256 != _digest(b""):
                raise CaptureProvenanceError("Error envelope mismatch")
        elif receipt.payload_kind == "raw_response_bytes":
            if not data or _digest(data) != receipt.raw_body_sha256:
                raise CaptureProvenanceError("Raw response mismatch")
        else:
            raise CaptureProvenanceError("Invalid payload kind")
        return data


@dataclass(frozen=True)
class CaptureBundle:
    """Unsealed DEVELOPMENT manifest; never derives its own TrustedSeal."""

    selection: bytes
    evidence_manifest: bytes
    blind_queue: bytes
    selected_snapshots: Mapping[str, bytes]
    all_receipts: tuple[Receipt, ...]

    def preflight_payloads(self) -> dict[str, bytes]:
        return {
            "selection": self.selection,
            "evidence_manifest": self.evidence_manifest,
            "blind_queue": self.blind_queue,
            **self.selected_snapshots,
        }


def build_capture_bundle(
    captures: Iterable[CapturedPage], *, store: CaptureStore,
    protocol: Mapping[str, Any], excluded_urls: Iterable[str],
    selected_at: str,
) -> CaptureBundle:
    """Persist all observations, then select without invoking any classifier.

    All excluded/duplicate/capped receipts appear in the evidence audit. Their
    bytes remain on disk; only selected bytes enter the preflight payload.
    """
    selected_instant = _instant(selected_at)
    entities = protocol["entities"]
    entity_ids = [entry["entity_id"] for entry in entities]
    if len(set(entity_ids)) != len(entity_ids) or not entity_ids:
        raise CaptureProvenanceError("Invalid/duplicate registered entities")
    sampling = protocol["sampling"]
    for key in (
        "max_pages_per_entity", "max_review_units_per_entity", "max_review_units",
        "minimum_review_units", "minimum_entities",
    ):
        if type(sampling.get(key)) is not int or sampling[key] <= 0:
            raise CaptureProvenanceError(f"Invalid sampling limit: {key}")
    by_entity: dict[str, list[CapturedPage]] = {key: [] for key in entity_ids}
    for capture in captures:
        capture.validate()
        if capture.entity_id not in by_entity:
            raise CaptureProvenanceError("Unregistered capture entity")
        if selected_instant < _instant(capture.captured_at):
            raise CaptureProvenanceError("Capture after selection time")
        by_entity[capture.entity_id].append(capture)
    blocked = {url_identity(url) for url in excluded_urls}
    seen: set[str] = set()
    selected: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    blind: list[dict[str, Any]] = []
    audit: list[dict[str, Any]] = []
    selected_snapshots: dict[str, bytes] = {}
    receipts: list[Receipt] = []
    global_order = 0
    for entry in entities:
        entity_id, expected_root = entry["entity_id"], entry["root_url"]
        pages = sorted(by_entity[entity_id], key=lambda page: page.discovery_index)
        if (
            len(pages) > sampling["max_pages_per_entity"]
            or [page.discovery_index for page in pages] != list(range(len(pages)))
        ):
            raise CaptureProvenanceError(
                "Missing, duplicate or excessive traversal indices"
            )
        chosen = 0
        for page in pages:
            if page.root_url != expected_root:
                raise CaptureProvenanceError("Root URL mismatch")
            receipt = store.persist(page)
            receipts.append(receipt)
            keys = {url_identity(page.requested_url)}
            if page.final_url is not None:
                keys.add(url_identity(page.final_url))
            duplicate = bool(keys & seen)
            seen.update(keys)
            if keys & blocked:
                reason = "known_url"
            elif duplicate:
                reason = "duplicate"
            elif chosen >= sampling["max_review_units_per_entity"]:
                reason = "entity_cap"
            elif len(selected) >= sampling["max_review_units"]:
                reason = "global_cap"
            else:
                reason = "selected"
                chosen += 1
                selection_row = {
                    "review_unit_id": receipt.review_unit_id,
                    "entity_id": entity_id,
                    "root_url": expected_root,
                    "page_url": receipt.page_url,
                    "requested_url": receipt.requested_url,
                    "snapshot_reference": receipt.snapshot_reference,
                    "discovery_index": receipt.discovery_index,
                    "global_discovery_order": global_order,
                }
                selected.append(selection_row)
                evidence.append({
                    **selection_row,
                    "final_url": receipt.final_url,
                    "captured_at": receipt.captured_at,
                    "snapshot_sha256": receipt.snapshot_sha256,
                    "raw_body_sha256": receipt.raw_body_sha256,
                    "capture_state": receipt.capture_state,
                    "http_status_code": receipt.http_status_code,
                    "media_type": receipt.media_type,
                    "payload_kind": receipt.payload_kind,
                })
                blind.append({
                    "review_unit_id": receipt.review_unit_id,
                    "entity_id": entity_id,
                    "root_url": expected_root,
                    "page_url": receipt.page_url,
                    "snapshot_reference": receipt.snapshot_reference,
                    "observed_at": receipt.captured_at,
                    "review_status": "pending",
                    **dict.fromkeys(_HUMAN_FIELDS, None),
                })
                material = store.load(receipt)
                previous = selected_snapshots.get(receipt.snapshot_reference)
                if previous is not None and previous != material:
                    raise CaptureProvenanceError("Snapshot digest collision")
                selected_snapshots[receipt.snapshot_reference] = material
            audit.append({
                **receipt.document(), "reason": reason,
                "global_discovery_order": global_order,
            })
            global_order += 1
    counts = Counter(row["entity_id"] for row in selected)
    sufficient = (
        len(selected) >= sampling["minimum_review_units"]
        and len(counts) >= sampling["minimum_entities"]
    )
    selection_doc = {
        "status": "sufficient" if sufficient else "insufficient_sample",
        "selected_at": selected_at,
        "units": selected,
    }
    evidence_doc = {
        "units": evidence, "audit": audit,
        "audit_scope": "all_collector_observations_before_caps",
    }
    return CaptureBundle(
        selection=_json(selection_doc),
        evidence_manifest=_json(evidence_doc),
        blind_queue=_json({"units": blind if sufficient else []}),
        selected_snapshots=selected_snapshots if sufficient else {},
        all_receipts=tuple(receipts),
    )


def verify_capture_bundle(
    bundle: CaptureBundle, store: CaptureStore, *,
    payloads: Mapping[str, bytes],
) -> None:
    """Re-read every raw/receipt file, including excluded and capped captures."""
    if any(
        payloads.get(name) != content
        for name, content in bundle.preflight_payloads().items()
    ):
        raise CaptureProvenanceError("Candidate payload differs from capture bundle")
    try:
        manifest = json.loads(bundle.evidence_manifest)
        audit = manifest["audit"]
        selected_units = json.loads(bundle.selection)["units"]
        if len(audit) != len(bundle.all_receipts):
            raise CaptureProvenanceError("Incomplete capture audit")
        selected_audit: list[dict[str, Any]] = []
        expected_snapshots: set[str] = set()
        for index, (row, receipt) in enumerate(
            zip(audit, bundle.all_receipts)
        ):
            if row != {
                **receipt.document(), "reason": row.get("reason"),
                "global_discovery_order": index,
            }:
                raise CaptureProvenanceError("Capture audit/order mismatch")
            if row["reason"] not in {
                "selected", "known_url", "duplicate", "entity_cap", "global_cap"
            }:
                raise CaptureProvenanceError("Invalid exclusion reason")
            material = store.load(receipt)
            if row["reason"] == "selected":
                selected_audit.append(row)
                expected_snapshots.add(receipt.snapshot_reference)
                if payloads.get(receipt.snapshot_reference) != material:
                    raise CaptureProvenanceError(
                        "Selected snapshot differs from durable evidence"
                    )
        if len(selected_audit) != len(selected_units):
            raise CaptureProvenanceError("Selected audit count mismatch")
        for row, audit_row, evidence in zip(
            selected_units, selected_audit, manifest["units"]
        ):
            for key in (
                "review_unit_id", "entity_id", "root_url", "page_url",
                "requested_url", "snapshot_reference", "discovery_index",
                "global_discovery_order",
            ):
                if (
                    key not in audit_row or row[key] != audit_row[key]
                    or row[key] != evidence[key]
                ):
                    raise CaptureProvenanceError(
                        "Selection/audit/evidence identity mismatch"
                    )
            for key in ("snapshot_sha256", "captured_at", "final_url"):
                if evidence[key] != audit_row[key]:
                    raise CaptureProvenanceError("Evidence metadata mismatch")
        if len(manifest["units"]) != len(selected_units):
            raise CaptureProvenanceError("Incomplete selected evidence")
        if set(bundle.selected_snapshots) != expected_snapshots:
            raise CaptureProvenanceError("Selected snapshot set mismatch")
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise CaptureProvenanceError("Malformed capture manifest") from exc


def guarded_capture_development_evaluate(
    payloads: Mapping[str, bytes], *, bundle: CaptureBundle, store: CaptureStore,
    trusted: Any, observed_commit: str, evaluator: Callable[..., Any],
) -> dict[str, Any]:
    """No metric call until durable evidence AND original preflight pass."""
    verify_capture_bundle(bundle, store, payloads=payloads)
    from .val009_preflight import guarded_development_evaluate

    return guarded_development_evaluate(
        payloads, trusted=trusted, observed_commit=observed_commit,
        evaluator=evaluator,
    )
