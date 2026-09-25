"""Fail-closed VAL-009 technical preflight; never certifies a scientific freeze.

This module is intentionally independent from the candidate and metrics modules.
A caller may invoke an evaluator only *after* every integrity check has passed.
A trusted seal must come from a separately preserved, access-controlled source;
this module cannot authenticate a self-declared witness or enforce vault access.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from typing import Any, Callable, Mapping

_PROTOCOL_ID = "MAR-T2A-M3-VAL-009-PROTOCOL"
_EXPERIMENT_ID = "MAR-T2A-M3-VAL-009"
_REQUIRED = frozenset({
    "protocol", "candidate_wrapper", "base_classifier", "collector", "config",
    "selector", "evaluator", "dependencies", "exclusions", "codebook",
    "selection", "evidence_manifest", "blind_queue", "predictions",
    "human_reviews", "prediction_freeze", "human_freeze", "disclosure",
})
_JSON_NAMES = frozenset({
    "protocol", "selection", "evidence_manifest", "blind_queue", "predictions",
    "human_reviews", "prediction_freeze", "human_freeze", "disclosure",
})
_HASH = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT_HASH = re.compile(r"[0-9a-f]{40}\Z")
_HUMAN_QUEUE_FIELDS = frozenset({
    "review_unit_id", "entity_id", "page_url", "root_url", "parent_url",
    "snapshot_reference", "observed_at", "human_surface_type",
    "human_is_item_level", "human_access_state", "human_review_note",
    "reviewer_id", "reviewed_at", "review_status",
})


class PreflightFailure(ValueError):
    """Hard failure: no evaluator may run or consume predictions."""


@dataclass(frozen=True)
class TrustedSeal:
    """External expected state; do not populate it from untrusted run artifacts."""

    protocol_id: str
    experiment_id: str
    protocol_version: str
    candidate_version: str
    commit_sha: str
    sealed_at: str
    witness_reference: str
    custodian_id: str
    reviewer_id: str
    restricted_store_reference: str
    pins: Mapping[str, str]


@dataclass(frozen=True)
class VerifiedInputs:
    """In-memory verified rows, never a declaration of independent validation."""

    expected: tuple[dict[str, Any], ...]
    humans: tuple[dict[str, Any], ...]
    predictions: tuple[dict[str, Any], ...]
    protocol: dict[str, Any]


def _fail(message: str) -> None:
    raise PreflightFailure(message)


def _required_text(value: Any, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(f"Missing {description}")
    return value


def _instant(value: Any, description: str) -> datetime:
    raw = _required_text(value, description)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PreflightFailure(f"Invalid timestamp: {description}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"Timezone required: {description}")
    return parsed


def _object(value: Any, description: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"Expected object: {description}")
    return value


def _units(document: dict[str, Any], name: str) -> list[dict[str, Any]]:
    rows = document.get("units")
    if not isinstance(rows, list) or not rows:
        _fail(f"Missing units: {name}")
    for row in rows:
        _object(row, f"{name} unit")
    return rows


def _identity(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _required_text(row.get("review_unit_id"), "review_unit_id"),
        _required_text(row.get("entity_id"), "entity_id"),
        _required_text(row.get("page_url"), "page_url"),
        _required_text(row.get("snapshot_reference"), "snapshot_reference"),
    )


def _index(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        identity = _identity(row)
        if identity[0] in indexed:
            _fail(f"Duplicate review ID: {label}")
        indexed[identity[0]] = row
    return indexed


def _same_units(
    source: dict[str, dict[str, Any]], other: dict[str, dict[str, Any]], label: str
) -> None:
    if set(source) != set(other):
        _fail(f"Missing or extra review IDs: {label}")
    for item_id, row in source.items():
        if _identity(row) != _identity(other[item_id]):
            _fail(f"Mismatched unit identity: {label}")


def verify_preflight(
    payloads: Mapping[str, bytes], *, trusted: TrustedSeal, observed_commit: str
) -> VerifiedInputs:
    """Check all pinned bytes, identities, reviews and ordered freeze events.

    The external provenance of ``trusted`` and actual access-control policy need
    independent operational verification. Draft protocols always fail closed.
    """
    if trusted.protocol_id != _PROTOCOL_ID or trusted.experiment_id != _EXPERIMENT_ID:
        _fail("Unexpected VAL-009 identity")
    if trusted.protocol_version != "2.3.0" or trusted.candidate_version != "2.3.0-dev":
        _fail("Unexpected protocol or candidate version")
    if not _COMMIT_HASH.fullmatch(trusted.commit_sha) or observed_commit != trusted.commit_sha:
        _fail("Commit mismatch")
    if not all((trusted.witness_reference, trusted.custodian_id, trusted.reviewer_id,
                trusted.restricted_store_reference)):
        _fail("Missing externally controlled witness or custodian metadata")
    if trusted.custodian_id == trusted.reviewer_id:
        _fail("Custodian and reviewer must be different")
    if not trusted.restricted_store_reference.startswith("restricted://"):
        _fail("Private prediction store must be separately declared")
    sealed_at = _instant(trusted.sealed_at, "external seal time")

    snapshot_names = set(payloads) - _REQUIRED
    if any(not name.startswith("snapshot/") for name in snapshot_names):
        _fail("Unexpected artifact")
    if not snapshot_names or set(payloads) != set(trusted.pins) or not _REQUIRED <= set(payloads):
        _fail("Missing, extra or unpinned artifact")
    for name, data in payloads.items():
        expected_hash = trusted.pins[name]
        if (not isinstance(data, bytes) or not data or not isinstance(expected_hash, str)
                or not _HASH.fullmatch(expected_hash)):
            _fail(f"Invalid artifact or digest: {name}")
        if sha256(data).hexdigest() != expected_hash:
            _fail(f"SHA-256 mismatch: {name}")

    decoded: dict[str, dict[str, Any]] = {}
    for name in _JSON_NAMES:
        try:
            decoded[name] = _object(json.loads(payloads[name]), name)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PreflightFailure(f"Invalid JSON: {name}") from exc

    protocol = decoded["protocol"]
    expected_metadata = {
        "protocol_id": trusted.protocol_id, "experiment_id": trusted.experiment_id,
        "protocol_version": trusted.protocol_version,
        "candidate_version": trusted.candidate_version,
        "candidate_commit": trusted.commit_sha, "status": "sealed",
    }
    for key, value in expected_metadata.items():
        if protocol.get(key) != value:
            _fail(f"Unsealed protocol or identity mismatch: {key}")
    blinding = _object(protocol.get("blinding"), "blinding contract")
    if (not isinstance(blinding.get("human_queue_allowed_fields"), list)
            or set(blinding["human_queue_allowed_fields"]) != _HUMAN_QUEUE_FIELDS
            or len(blinding["human_queue_allowed_fields"]) != len(_HUMAN_QUEUE_FIELDS)):
        _fail("Blinding contract mismatch")
    if protocol.get("candidate_reference_is_freeze") is not True:
        _fail("Candidate is not frozen")
    labels = _object(protocol.get("labels"), "protocol labels")
    surfaces = labels.get("surface_types")
    accesses = labels.get("access_states")
    positives = labels.get("item_positive")
    if any(not isinstance(v, list) or not v for v in (surfaces, accesses, positives)):
        _fail("Missing label vocabularies")
    sampling = _object(protocol.get("sampling"), "sampling policy")
    for key in ("minimum_review_units", "minimum_entities", "max_review_units_per_entity", "max_review_units"):
        if not isinstance(sampling.get(key), int) or sampling[key] <= 0:
            _fail(f"Invalid sampling contract: {key}")

    selection = decoded["selection"]
    if selection.get("status") != "sufficient":
        _fail("Insufficient or unsealed sample")
    selected_at = _instant(selection.get("selected_at"), "selection time")
    if not sealed_at < selected_at:
        _fail("Sampling preceded protocol seal")
    expected = _index(_units(selection, "selection"), "selection")
    entity_counts = Counter(row["entity_id"] for row in expected.values())
    if (len(expected) < sampling["minimum_review_units"]
            or len(expected) > sampling["max_review_units"]
            or len(entity_counts) < sampling["minimum_entities"]
            or max(entity_counts.values()) > sampling["max_review_units_per_entity"]):
        _fail("Sample violates preregistered bounds")

    evidence = _index(_units(decoded["evidence_manifest"], "evidence"), "evidence")
    _same_units(expected, evidence, "evidence")
    for item_id, row in expected.items():
        requested = _required_text(row.get("requested_url"), "requested URL")
        if requested != _required_text(evidence[item_id].get("requested_url"), "evidence requested URL"):
            _fail("Requested URL was lost or substituted")
    referenced = set()
    for row in evidence.values():
        name = row["snapshot_reference"]
        referenced.add(name)
        if (name not in snapshot_names or row.get("snapshot_sha256") != trusted.pins[name]):
            _fail("Snapshot bytes or reference mismatch")
        captured_at = _instant(row.get("captured_at"), "snapshot capture time")
        if not sealed_at < captured_at <= selected_at:
            _fail("Snapshot is outside the sealed collection period")
    if referenced != snapshot_names:
        _fail("Unused or unaccounted raw snapshot")

    queue = decoded["blind_queue"]
    blinded = _index(_units(queue, "blind queue"), "blind queue")
    _same_units(expected, blinded, "blind queue")
    if set(queue) != {"units"}:
        _fail("Unrecognized blind-queue metadata")
    for row in blinded.values():
        if not set(row) <= _HUMAN_QUEUE_FIELDS or any(
            row.get(name) is not None for name in (
                "human_surface_type", "human_is_item_level", "human_access_state",
                "human_review_note", "reviewer_id", "reviewed_at"
            )
        ) or row.get("review_status") != "pending":
            _fail("Blind queue leaks prediction/annotation or has unknown fields")

    predicted = _index(_units(decoded["predictions"], "predictions"), "predictions")
    reviewed = _index(_units(decoded["human_reviews"], "human reviews"), "human reviews")
    _same_units(expected, predicted, "predictions")
    _same_units(expected, reviewed, "human reviews")
    for row in predicted.values():
        if row.get("predicted_surface_type") not in surfaces or row.get("predicted_access_state") not in accesses:
            _fail("Invalid prediction label")
        if row.get("predicted_item_level") is not (
            row["predicted_surface_type"] in positives
        ):
            _fail("Invalid predicted item mapping")

    prediction_freeze = decoded["prediction_freeze"]
    human_freeze = decoded["human_freeze"]
    disclosure = decoded["disclosure"]
    if (prediction_freeze.get("predictions_sha256") != trusted.pins["predictions"]
            or prediction_freeze.get("selection_sha256") != trusted.pins["selection"]
            or prediction_freeze.get("protocol_sha256") != trusted.pins["protocol"]
            or prediction_freeze.get("candidate_commit") != trusted.commit_sha
            or prediction_freeze.get("custodian_id") != trusted.custodian_id):
        _fail("Prediction freeze provenance mismatch")
    prediction_at = _instant(prediction_freeze.get("frozen_at"), "prediction freeze")
    review_start = _instant(human_freeze.get("review_started_at"), "review start")
    human_at = _instant(human_freeze.get("frozen_at"), "human freeze")
    opened_at = _instant(disclosure.get("opened_at"), "prediction disclosure")
    if not selected_at < prediction_at < review_start < human_at < opened_at:
        _fail("Freeze and disclosure chronology violation")
    for row in reviewed.values():
        if (row.get("review_status") != "complete"
                or row.get("reviewer_id") != trusted.reviewer_id
                or not isinstance(row.get("human_review_note"), str)
                or not row["human_review_note"].strip()
                or row.get("human_surface_type") not in surfaces
                or row.get("human_access_state") not in accesses):
            _fail("Incomplete or incompatible human review")
        surface = row["human_surface_type"]
        expected_item = None if surface == "unknown" else surface in positives
        if row.get("human_is_item_level") is not expected_item:
            _fail("Invalid human item mapping")
        reviewed_at = _instant(row.get("reviewed_at"), "human review time")
        if not review_start <= reviewed_at < human_at:
            _fail("Human review outside blinded review period")
    if (human_freeze.get("reviews_sha256") != trusted.pins["human_reviews"]
            or human_freeze.get("selection_sha256") != trusted.pins["selection"]
            or human_freeze.get("reviewer_id") != trusted.reviewer_id
            or disclosure.get("human_freeze_sha256") != trusted.pins["human_freeze"]
            or disclosure.get("predictions_sha256") != trusted.pins["predictions"]
            or disclosure.get("custodian_id") != trusted.custodian_id):
        _fail("Human freeze or disclosure provenance mismatch")
    return VerifiedInputs(
        expected=tuple(expected.values()), humans=tuple(reviewed.values()),
        predictions=tuple(predicted.values()), protocol=protocol,
    )


def guarded_development_evaluate(
    payloads: Mapping[str, bytes], *, trusted: TrustedSeal, observed_commit: str,
    evaluator: Callable[..., Any]
) -> dict[str, Any]:
    """Call a development evaluator *only* after a full successful preflight.

    This is NOT the official VAL-009 executor. In particular, it cannot prove
    independent witness authenticity, physical prediction secrecy, or code seal.
    """
    verified = verify_preflight(payloads, trusted=trusted, observed_commit=observed_commit)
    result = evaluator(
        list(verified.expected), list(verified.humans), list(verified.predictions),
        protocol=verified.protocol,
    )
    return {"mode": "development_dry_run_only", "independent_validation": False,
            "m4_scaling_allowed": False, "development_metrics": result}
