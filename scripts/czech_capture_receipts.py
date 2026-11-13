"""Czech TV capture-receipt protocol: offline, metadata-only, fail closed.

This module NEVER sends HTTP requests or reads external pages. It accepts
responses supplied in memory by an isolated test or a *future reviewed adapter*,
hashes the bytes and records minimal, non-sensitive metadata. A receipt alone
does not prove that the bytes came from the alleged source, nor that a public
catalogue was enumerated to exhaustion. It cannot admit production data.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from urllib.parse import parse_qsl, urlparse

from scripts.audit_czech_completeness_v2 import ID, official_url

SCHEMA = "mar.czech.capture-receipt.v1"
MAX_BODY_BYTES = 512 * 1024
MAX_IDS = 2000
# Query keys not on this list could expose tokens or change the scope.
PAGINATION_KEYS = frozenset({"page", "stranka", "offset"})
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(value).hexdigest()


def _url_allowed(url):
    if not official_url(url):
        return False
    parsed = urlparse(url)
    if not parsed.query:
        return True
    try:
        params = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    return bool(params) and len(params) <= 2 and all(
        key in PAGINATION_KEYS and value.isascii() and value.isdecimal()
        and len(value) <= 8
        for key, value in params
    ) and len(set(key for key, _ in params)) == len(params)


def _time_utc(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("capture timestamp must have a timezone")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validate_claims(*, page_index, declared_total, record_ids,
                     terminal, next_page_index):
    if type(page_index) is not int or page_index < 0:
        raise ValueError("invalid page index")
    if type(declared_total) is not int or declared_total <= 0:
        raise ValueError("invalid source-reported total")
    if not isinstance(record_ids, list) or not 1 <= len(record_ids) <= MAX_IDS:
        raise ValueError("invalid number of record identifiers")
    if any(not isinstance(i, str) or not ID.fullmatch(i) for i in record_ids):
        raise ValueError("invalid public episode ID")
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("duplicate ID on one page")
    if type(terminal) is not bool:
        raise ValueError("terminal flag must be boolean")
    if terminal:
        if next_page_index is not None:
            raise ValueError("terminal page cannot point to next page")
    elif type(next_page_index) is not int or next_page_index != page_index + 1:
        raise ValueError("non-terminal page must point to the next index")


def capture_receipt(*, page_index, requested_url, final_url, http_status,
                    response_body, captured_at, content_type, declared_total,
                    record_ids, terminal, next_page_index, code_revision):
    """Build a minimal receipt from *supplied* bytes; no access to a URL.

    The metadata extracted by the caller is a CLAIM until a separate auditor
    re-extracts it from independently preserved source evidence.
    """
    if not _url_allowed(requested_url) or requested_url != final_url:
        raise ValueError("official HTTPS URL required, no redirects")
    if type(http_status) is not int or http_status != 200:
        raise ValueError("only successful HTTP 200 responses are eligible")
    if not isinstance(response_body, bytes) or not 1 <= len(response_body) <= MAX_BODY_BYTES:
        raise ValueError("response must be bounded nonempty bytes")
    if content_type not in ("text/html", "application/json"):
        raise ValueError("unexpected content type")
    if not isinstance(code_revision, str) or not COMMIT.fullmatch(code_revision):
        raise ValueError("full code revision SHA required")
    _validate_claims(
        page_index=page_index, declared_total=declared_total,
        record_ids=record_ids, terminal=terminal,
        next_page_index=next_page_index,
    )
    receipt = {
        "schema": SCHEMA,
        "source": "czech_tv",
        "observation_level": "supplied_bytes_unattested",
        "source_attested": False,
        "corpus_complete": False,
        "production_gate": "HOLD",
        "media_downloaded": False,
        "raw_response_persisted": False,
        "code_revision": code_revision,
        "captured_at_utc": _time_utc(captured_at),
        "request": {"method": "GET", "url": requested_url, "redirected": False},
        "response": {
            "final_url": final_url,
            "http_status": http_status,
            "content_type": content_type,
            "byte_count": len(response_body),
            "body_sha256": digest(response_body),
        },
        "page": {
            "page_index": page_index,
            "declared_total_claim": declared_total,
            "record_ids_claim": list(record_ids),
            "terminal_claim": terminal,
            "next_page_index_claim": next_page_index,
        },
    }
    return receipt


def audit_receipt(receipt, *, independently_pinned_sha256=None, raw_body=None):
    """Audit internal receipt integrity, optionally replaying supplied bytes.

    Independent SHA pinning detects changes after a pin was created; neither
    pinning nor replay can establish HTTP/TLS source authenticity on its own.
    """
    result = {
        "receipt_integrity_ok": False,
        "external_anchor_match": False,
        "body_digest_replayed": False,
        "source_attested": False,
        "corpus_complete": False,
        "production_gate": "HOLD",
        "reasons": [],
    }
    errors = result["reasons"]
    if not isinstance(receipt, dict):
        errors.append("receipt_not_object")
        return result
    try:
        if set(receipt) != {
            "schema", "source", "observation_level", "source_attested",
            "corpus_complete", "production_gate", "media_downloaded",
            "raw_response_persisted", "code_revision", "captured_at_utc",
            "request", "response", "page",
        }:
            raise ValueError("unexpected_receipt_fields")
        if receipt["schema"] != SCHEMA or receipt["source"] != "czech_tv":
            raise ValueError("unexpected_receipt_schema")
        if (receipt["source_attested"] is not False
                or receipt["observation_level"] != "supplied_bytes_unattested"
                or receipt["corpus_complete"] is not False
                or receipt["production_gate"] != "HOLD"
                or receipt["media_downloaded"] is not False
                or receipt["raw_response_persisted"] is not False):
            raise ValueError("forbidden_certification_claim")
        if not COMMIT.fullmatch(receipt["code_revision"]):
            raise ValueError("invalid_revision")
        timestamp = receipt["captured_at_utc"]
        if (not isinstance(timestamp, str) or not timestamp.endswith("Z")
                or datetime.fromisoformat(timestamp.replace("Z", "+00:00")).utcoffset().total_seconds() != 0):
            raise ValueError("invalid_utc_timestamp")
        request, response, page = receipt["request"], receipt["response"], receipt["page"]
        if set(request) != {"method", "url", "redirected"} or request["method"] != "GET" or request["redirected"] is not False:
            raise ValueError("invalid_request")
        if set(response) != {"final_url", "http_status", "content_type", "byte_count", "body_sha256"}:
            raise ValueError("invalid_response")
        if not _url_allowed(request["url"]) or request["url"] != response["final_url"]:
            raise ValueError("url_not_official_or_redirected")
        if (type(response["http_status"]) is not int or response["http_status"] != 200
                or response["content_type"] not in ("text/html", "application/json")
                or type(response["byte_count"]) is not int
                or not 1 <= response["byte_count"] <= MAX_BODY_BYTES
                or not isinstance(response["body_sha256"], str)
                or not SHA256.fullmatch(response["body_sha256"])):
            raise ValueError("invalid_bounded_response")
        if set(page) != {"page_index", "declared_total_claim", "record_ids_claim",
                         "terminal_claim", "next_page_index_claim"}:
            raise ValueError("unexpected_page_fields")
        _validate_claims(
            page_index=page["page_index"],
            declared_total=page["declared_total_claim"],
            record_ids=page["record_ids_claim"],
            terminal=page["terminal_claim"],
            next_page_index=page["next_page_index_claim"],
        )
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError) as error:
        errors.append("receipt_schema_or_claim_invalid")
        return result

    result["receipt_integrity_ok"] = True
    if (isinstance(independently_pinned_sha256, str)
            and SHA256.fullmatch(independently_pinned_sha256)
            and digest(canonical(receipt).encode("utf-8")) == independently_pinned_sha256):
        result["external_anchor_match"] = True
    else:
        errors.append("independent_receipt_pin_missing_or_mismatched")
    if raw_body is None:
        errors.append("raw_body_not_available_for_independent_replay")
    elif (isinstance(raw_body, bytes)
          and len(raw_body) == receipt["response"]["byte_count"]
          and digest(raw_body) == receipt["response"]["body_sha256"]):
        result["body_digest_replayed"] = True
    else:
        errors.append("body_digest_mismatch")
    errors.append("source_origin_not_independently_attested")
    return result
