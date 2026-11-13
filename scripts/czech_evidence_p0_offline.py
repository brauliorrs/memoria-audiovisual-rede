"""Offline, *synthetic-only* encrypted evidence bundle for Czech v2 replay.

No network, object storage or filesystem writes are performed here. This is a
portable encryption / restore DRY RUN contract for already supplied synthetic
metadata. It never authorizes actual capture, production backup, full-corpus
enumeration, P0 approval or media processing. A real backend requires separate
review of source-data minimization, provenance, IAM, key management, retention,
cross-host backups and disaster recovery.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from scripts.czech_capture_receipts import canonical
from scripts.replay_czech_receipts_v2 import (
    MAX_PAGES_TO_REPLAY, replay_receipts_to_v2,
)

MAGIC = b"MAR-CZECH-EVIDENCE-P0-OFFLINE-V1\0"
SCHEMA = "mar.czech.evidence-p0-offline.v1"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
SCOPE_ID = re.compile(r"[a-z0-9][a-z0-9_-]{5,63}\Z")
MAX_UNSEALED = 12 * 1024 * 1024
MAX_SEALED = MAX_UNSEALED + 8192
MAX_HEADER = 2048


class EvidenceRejected(ValueError):
    """Use stable reason codes; never emit secret keys or HTML content."""


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _key(key: bytes):
    if not isinstance(key, bytes) or len(key) != 32:
        raise EvidenceRejected("key_must_be_32_bytes")
    return key


def _scope(scope_id: str):
    if not isinstance(scope_id, str) or not SCOPE_ID.fullmatch(scope_id):
        raise EvidenceRejected("scope_id_not_safe")
    return scope_id


def _sha(value: str):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise EvidenceRejected("external_sha256_invalid")
    return value


def _replay(data):
    report = replay_receipts_to_v2(
        receipts=data["receipts"],
        bodies=data["bodies"],
        receipt_sha256_pins=data["receipt_pins"],
        manifest=data["manifest"],
        manifest_sha256_pin=data["manifest_pin"],
        output_urls=data["output_urls"],
    )
    if not all((report["bridge_replay_consistent"],
                report["v2_structural_pass"],
                report["v2_manifest_anchor_match"],
                report["v2_output_reconciled"])):
        raise EvidenceRejected("offline_replay_inconsistent")
    if (report["source_attested"] is not False
            or report["corpus_complete"] is not False
            or report["production_gate"] != "HOLD"):
        raise EvidenceRejected("replay_not_fail_closed")
    return report


def seal_synthetic_bundle(
    *, receipts, bodies, receipt_pins, manifest,
    manifest_pin, output_urls, scope_id, key,
):
    """Validate, seal supplied synthetic evidence; return bytes (not a file).

    Do NOT feed real captured provider HTML or tokens into this prototype.
    A random nonce is generated per invocation. Never reuse the key+nonce pair.
    """
    _key(key)
    _scope(scope_id)
    _sha(manifest_pin)
    if (not isinstance(receipts, list) or not isinstance(bodies, list)
            or not isinstance(receipt_pins, list)
            or not 1 <= len(receipts) <= MAX_PAGES_TO_REPLAY
            or len(receipts) != len(bodies)
            or len(receipts) != len(receipt_pins)
            or not all(isinstance(body, bytes) for body in bodies)):
        raise EvidenceRejected("bundle_pages_invalid")
    if not all(isinstance(pin, str) and SHA256.fullmatch(pin) for pin in receipt_pins):
        raise EvidenceRejected("receipt_pins_invalid")

    data = {
        "receipts": receipts, "bodies": bodies,
        "receipt_pins": receipt_pins,
        "manifest": manifest, "manifest_pin": manifest_pin,
        "output_urls": output_urls,
    }
    review = _replay(data)
    payload = {
        "schema": SCHEMA,
        "synthetic_only": True,
        "source_attested": False,
        "corpus_complete": False,
        "production_gate": "HOLD",
        "scope_id": scope_id,
        "manifest": manifest,
        "manifest_pin": manifest_pin,
        "receipts": receipts,
        "receipt_pins": receipt_pins,
        "bodies_base64": [base64.b64encode(body).decode("ascii") for body in bodies],
        "output_urls": output_urls,
    }
    try:
        plaintext = canonical(payload).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvidenceRejected("bundle_canonicalization_failed") from exc
    if not 1 <= len(plaintext) <= MAX_UNSEALED:
        raise EvidenceRejected("bundle_plaintext_exceeds_limit")

    header = {
        "schema": SCHEMA, "scope_id": scope_id,
        "manifest_pin": manifest_pin,
        "page_count": len(receipts),
        "plaintext_sha256": _hash(plaintext),
    }
    aad = canonical(header).encode("utf-8")
    if len(aad) > MAX_HEADER:
        raise EvidenceRejected("header_exceeds_limit")
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
    sealed = MAGIC + struct.pack(">I", len(aad)) + aad + nonce + ciphertext
    if len(sealed) > MAX_SEALED:
        raise EvidenceRejected("encrypted_bundle_exceeds_limit")
    return sealed, {
        "status": "synthetic_encrypted_in_memory",
        "encrypted_sha256": _hash(sealed),
        "receipt_count": len(receipts),
        "reextracted_unique_records": review["reextracted_unique_records"],
        "offline_replay_consistent": True,
        "source_attested": False,
        "corpus_complete": False,
        "durability_verified": False,
        "production_gate": "HOLD",
    }


def unseal_and_replay_synthetic_bundle(
    sealed, *, key, expected_scope_id, expected_manifest_pin,
    expected_receipt_pins, independently_pinned_encrypted_sha256,
):
    """Decrypt and replay only if ALL external anchors match.

    Plaintext is returned only to the caller's memory; no files are written.
    Output review is NOT a real remote-backup or provider-origin attestation.
    """
    _key(key)
    _scope(expected_scope_id)
    _sha(expected_manifest_pin)
    _sha(independently_pinned_encrypted_sha256)
    if (not isinstance(expected_receipt_pins, list)
            or not 1 <= len(expected_receipt_pins) <= MAX_PAGES_TO_REPLAY
            or not all(isinstance(p, str) and SHA256.fullmatch(p) for p in expected_receipt_pins)):
        raise EvidenceRejected("independent_receipt_pins_invalid")
    if (not isinstance(sealed, bytes) or len(sealed) > MAX_SEALED
            or not sealed.startswith(MAGIC)
            or _hash(sealed) != independently_pinned_encrypted_sha256):
        raise EvidenceRejected("encrypted_blob_missing_or_digest_mismatch")
    start = len(MAGIC)
    if len(sealed) < start + 4 + 12 + 16:
        raise EvidenceRejected("encrypted_blob_truncated")
    header_size = struct.unpack(">I", sealed[start:start + 4])[0]
    start += 4
    if not 1 <= header_size <= MAX_HEADER or len(sealed) < start + header_size + 12 + 16:
        raise EvidenceRejected("invalid_encrypted_header")
    aad = sealed[start:start + header_size]
    try:
        header = json.loads(aad)
    except (ValueError, TypeError) as exc:
        raise EvidenceRejected("invalid_encrypted_header_json") from exc
    if (not isinstance(header, dict) or set(header) != {
        "schema", "scope_id", "manifest_pin", "page_count", "plaintext_sha256"
    } or header["schema"] != SCHEMA
            or header["scope_id"] != expected_scope_id
            or header["manifest_pin"] != expected_manifest_pin
            or not isinstance(header["page_count"], int)
            or isinstance(header["page_count"], bool)
            or not 1 <= header["page_count"] <= MAX_PAGES_TO_REPLAY
            or not isinstance(header["plaintext_sha256"], str)
            or not SHA256.fullmatch(header["plaintext_sha256"])
            or canonical(header).encode("utf-8") != aad):
        raise EvidenceRejected("encrypted_header_not_canonical_or_untrusted")
    start += header_size
    nonce, ciphertext = sealed[start:start + 12], sealed[start + 12:]
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, aad)
    except (InvalidTag, ValueError) as exc:
        raise EvidenceRejected("gcm_authentication_failed") from exc
    if len(plaintext) > MAX_UNSEALED or _hash(plaintext) != header["plaintext_sha256"]:
        raise EvidenceRejected("decrypted_plaintext_digest_mismatch")
    try:
        payload = json.loads(plaintext)
        if (not isinstance(payload, dict) or set(payload) != {
            "schema", "synthetic_only", "source_attested", "corpus_complete",
            "production_gate", "scope_id", "manifest", "manifest_pin",
            "receipts", "receipt_pins", "bodies_base64", "output_urls",
        } or payload["schema"] != SCHEMA
                or payload["synthetic_only"] is not True
                or payload["source_attested"] is not False
                or payload["corpus_complete"] is not False
                or payload["production_gate"] != "HOLD"
                or payload["scope_id"] != expected_scope_id
                or payload["manifest_pin"] != expected_manifest_pin
                or payload["receipt_pins"] != expected_receipt_pins
                or len(payload["receipts"]) != header["page_count"]
                or len(payload["bodies_base64"]) != header["page_count"]):
            raise EvidenceRejected("restored_bundle_contract_invalid")
        bodies = [base64.b64decode(value, validate=True)
                  for value in payload["bodies_base64"]]
    except (TypeError, ValueError, KeyError) as exc:
        raise EvidenceRejected("restored_bundle_contract_invalid") from exc

    data = {
        "receipts": payload["receipts"],
        "bodies": bodies,
        "receipt_pins": payload["receipt_pins"],
        "manifest": payload["manifest"],
        "manifest_pin": payload["manifest_pin"],
        "output_urls": payload["output_urls"],
    }
    review = _replay(data)
    return data, {
        "status": "synthetic_restored_and_replayed_in_memory",
        "encrypted_sha256": _hash(sealed),
        "receipt_count": header["page_count"],
        "reextracted_unique_records": review["reextracted_unique_records"],
        "offline_replay_consistent": True,
        "source_attested": False,
        "corpus_complete": False,
        "durability_verified": False,
        "production_gate": "HOLD",
    }
