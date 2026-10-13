"""Operator-gated, OFFLINE recovery epochs for KAVI/Finna staging.

No API requests are issued here. A verified failure must be independently
adjudicated by the operator; the Finna adapter currently has NO confirmed
expired-token error classifier. An HTTP status or a guessed timezone alone
must never be treated as proof of expiration.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from memoria_audiovisual.digital_infrastructure.locking import FileWriteLock
from memoria_audiovisual.metadata_staging import (
    StageRejected, _atomic_json,
)
from scripts.audit_kavi_finna_staging import audit_finna_staging

SCHEMA = "kavi-finna-epoch-controller-1.0.0"
SHA = re.compile(r"^[0-9a-f]{64}$")
STATE = "epoch-controller.json"
ABORT_MARKER = "epoch-aborted.json"
RESTART_BUDGET = 1
CONFIRMED_REASON = "provider_confirmed_token_expired"


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fingerprint(value: str) -> bool:
    return isinstance(value, str) and SHA.fullmatch(value) is not None


def _epoch_dir(root: Path, number: int) -> Path:
    if number not in (1, 2):
        raise StageRejected("epoch_number_out_of_bounds")
    return root / "epochs" / f"epoch-{number:04d}"


def _lock_target(root: Path) -> Path:
    return root.parent / f".{root.name}-epoch-controller"


def _summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "active_epoch": state["active_epoch"],
        "restart_count": state["restart_count"],
        "restart_budget": RESTART_BUDGET,
        "prior_epochs": [
            {"number": row["number"], "state": row["state"]}
            for row in state["epochs"]
        ],
        "promotion_authorized": False,
        "media_downloaded": False,
        "network_requests_performed": 0,
        "note": "Offline workspace lifecycle only; no API or media access.",
    }


def _validate_state(root: Path, evidence_sha256: str) -> dict[str, Any]:
    try:
        state = json.loads((root / STATE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise StageRejected("epoch_state_unreadable") from exc
    if not isinstance(state, dict) or state.get("schema_version") != SCHEMA:
        raise StageRejected("epoch_state_schema_mismatch")
    if state.get("evidence_sha256") != evidence_sha256:
        raise StageRejected("epoch_scope_evidence_mismatch")
    if (state.get("promotion_authorized") is not False
        or state.get("media_downloaded") is not False):
        raise StageRejected("epoch_safety_gates_tampered")
    count = state.get("restart_count")
    active = state.get("active_epoch")
    epochs = state.get("epochs")
    if (not isinstance(count, int) or isinstance(count, bool)
        or count not in (0, 1) or active != count + 1
        or not isinstance(epochs, list) or len(epochs) != active):
        raise StageRejected("epoch_state_sequence_invalid")
    for index, entry in enumerate(epochs, start=1):
        if not isinstance(entry, dict) or entry.get("number") != index:
            raise StageRejected("epoch_state_number_invalid")
        expected = "active" if index == active else "aborted_confirmed_expiration"
        if entry.get("state") != expected:
            raise StageRejected("epoch_state_transition_invalid")
        if not _epoch_dir(root, index).is_dir():
            raise StageRejected("epoch_directory_missing")
        if index < active and not (_epoch_dir(root, index) / ABORT_MARKER).is_file():
            raise StageRejected("epoch_abort_marker_missing")
        if index == active and (_epoch_dir(root, index) / ABORT_MARKER).exists():
            raise StageRejected("active_epoch_is_aborted")
    return state


def initialize_epoch_workspace(
    root: str | Path, *, evidence_sha256: str,
) -> dict[str, Any]:
    """Create a new isolated epoch; refuse to reuse an existing directory."""
    if not _fingerprint(evidence_sha256):
        raise ValueError("invalid_epoch_scope_evidence_sha256")
    root = Path(root)
    if root.is_symlink():
        raise StageRejected("epoch_workspace_symlink_not_allowed")
    with FileWriteLock(_lock_target(root), timeout=10):
        if root.exists():
            raise StageRejected("epoch_workspace_already_exists")
        _epoch_dir(root, 1).mkdir(parents=True, exist_ok=False)
        state = {
            "schema_version": SCHEMA,
            "evidence_sha256": evidence_sha256,
            "active_epoch": 1,
            "restart_count": 0,
            "epochs": [{"number": 1, "state": "active"}],
            "promotion_authorized": False,
            "media_downloaded": False,
        }
        _atomic_json(root / STATE, state)
    return _summary(state)


def restart_after_confirmed_expiry(
    root: str | Path,
    *,
    evidence_sha256: str,
    expected_total: int,
    failure_reason: str,
    provider_response_sha256: str,
    provider_contract_sha256: str,
    operator_authorized: bool = False,
) -> dict[str, Any]:
    """Isolate a successor epoch only after *externally confirmed* expiration.

    This offline, manually adjudicated operation NEVER calls the API or copies
    records into a new epoch. It is intentionally not invoked by the current
    Finna runner: no authoritative server-expiry classifier exists yet.

    Attestation inputs are operational evidence, not a cryptographic signature
    or proof that the provider really emitted a particular error.
    """
    if not _fingerprint(evidence_sha256):
        raise ValueError("invalid_epoch_scope_evidence_sha256")
    if not isinstance(expected_total, int) or isinstance(expected_total, bool) or expected_total < 0:
        raise ValueError("invalid_epoch_expected_total")
    # A local clock prediction, 429, 5xx or generic 400 is NOT proof.
    if failure_reason != CONFIRMED_REASON:
        raise StageRejected("epoch_expiration_not_confirmed")
    if operator_authorized is not True:
        raise StageRejected("epoch_restart_requires_operator_approval")
    if not (_fingerprint(provider_response_sha256)
            and _fingerprint(provider_contract_sha256)):
        raise StageRejected("epoch_provider_expiry_evidence_unverified")
    root = Path(root)
    if root.is_symlink():
        raise StageRejected("epoch_workspace_symlink_not_allowed")
    with FileWriteLock(_lock_target(root), timeout=10):
        state = _validate_state(root, evidence_sha256)
        if state["restart_count"] >= RESTART_BUDGET:
            raise StageRejected("epoch_restart_budget_exhausted")
        old = _epoch_dir(root, state["active_epoch"])
        following = _epoch_dir(root, state["active_epoch"] + 1)
        if following.exists():
            raise StageRejected("epoch_successor_already_exists")
        checkpoint = old / "checkpoint.json"
        try:
            checkpoint_digest = _sha(checkpoint.read_bytes())
        except OSError as exc:
            raise StageRejected("epoch_checkpoint_missing") from exc
        # Replay immutable raw pages and source-normalized parity FIRST.
        audit = audit_finna_staging(
            old, evidence_sha256=evidence_sha256,
            expected_total=expected_total,
        )
        if audit["status"] != "partial" or audit["page_count"] < 1:
            raise StageRejected("epoch_cannot_restart_complete_or_empty")
        # Recheck under the same lock that protects the writer; do not accept
        # a checkpoint changed between initial anchor and successful replay.
        # Lock again and compare actual checkpoint digest to the audited state.
        # This rules out a cooperating writer changing it during adjudication.
        with FileWriteLock(old / "run", timeout=10):
            if (old / ABORT_MARKER).exists():
                raise StageRejected("epoch_already_aborted")
            if _sha(checkpoint.read_bytes()) != checkpoint_digest:
                raise StageRejected("epoch_checkpoint_changed_during_freeze")
            abort = {
                "schema_version": SCHEMA,
                "status": "aborted_confirmed_expiration",
                "checkpoint_sha256": checkpoint_digest,
                "record_count": audit["record_count"],
                "expected_total": expected_total,
                "source_record_id_sequence_sha256": audit["provenance_audit"]["record_id_sequence_sha256"],
                "provider_response_sha256": provider_response_sha256,
                "provider_contract_sha256": provider_contract_sha256,
                "operator_authorized": True,
                "promotion_authorized": False,
                "media_downloaded": False,
            }
            # Fail-closed order: freeze old epoch BEFORE creating new one.
            _atomic_json(old / ABORT_MARKER, abort)
            following.mkdir(parents=False, exist_ok=False)
            state["epochs"][-1] = {
                "number": state["active_epoch"],
                "state": "aborted_confirmed_expiration",
            }
            state["active_epoch"] += 1
            state["restart_count"] += 1
            state["epochs"].append({
                "number": state["active_epoch"], "state": "active",
            })
            _atomic_json(root / STATE, state)
    return _summary(state)


def inspect_epoch_workspace(
    root: str | Path, *, evidence_sha256: str,
) -> dict[str, Any]:
    """Read public lifecycle state without revealing records or token."""
    if not _fingerprint(evidence_sha256):
        raise ValueError("invalid_epoch_scope_evidence_sha256")
    root = Path(root)
    with FileWriteLock(_lock_target(root), timeout=10):
        state = _validate_state(root, evidence_sha256)
    return _summary(state)
