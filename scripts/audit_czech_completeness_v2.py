"""Offline v2 evidence audit for Czech TV. No network, media or production writes.

The manifest and page checkpoints are *claims* about official public pages.
Replaying hashes establishes consistency, NOT the authenticity of the source.
Even a fully consistent offline manifest cannot lift the production HOLD until
a separate, reviewed source-attestation and durable P0 gate exist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlparse

SOURCE_URL = "https://www.ceskatelevize.cz/ivysilani/"
SCHEMA = "mar.czech.completeness.v2"
GENESIS = hashlib.sha256(b"MAR-CZECH-COMPLETENESS-V2-GENESIS").hexdigest()
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
ID = re.compile(r"[0-9]{8,20}\Z")
EPISODE_PATH = re.compile(r"/porady/[0-9]{2,}-[a-z0-9-]+/([0-9]{8,20})/?\Z", re.I)
PAGE_FIELDS = frozenset((
    "page_index", "page_url", "response_sha256", "declared_total",
    "record_ids", "terminal", "terminal_reason", "next_page_index",
    "http_status", "error", "previous_chain_sha256", "chain_sha256",
))
MAX_PAGES = 256
MAX_RECORDS_PER_PAGE = 2000


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def digest_ok(value):
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def natural(value, *, positive=False):
    return (type(value) is int and value >= (1 if positive else 0))


def official_url(value, *, episode=False):
    if not isinstance(value, str):
        return False
    try:
        url = urlparse(value)
        if (url.scheme != "https" or url.hostname != "www.ceskatelevize.cz"
                or url.port not in (None, 443) or url.username or url.password
                or url.fragment):
            return False
        if episode:
            return EPISODE_PATH.fullmatch(url.path) is not None and not url.query
        return url.path.startswith(("/ivysilani/", "/porady/"))
    except ValueError:
        return False


def checkpoint(payload, previous=GENESIS):
    """Build a deterministic checkpoint for offline fixtures / future collectors."""
    if not isinstance(payload, dict) or "chain_sha256" in payload or "previous_chain_sha256" in payload:
        raise ValueError("page payload cannot contain hash-chain fields")
    if not digest_ok(previous):
        raise ValueError("invalid preceding hash")
    item = {**payload, "previous_chain_sha256": previous}
    item["chain_sha256"] = hashlib.sha256(
        (previous + canonical(payload)).encode("utf-8")
    ).hexdigest()
    return item


def audit(manifest, pages, *, trusted_manifest_sha256=None, output_urls=None):
    """Audit a bounded official selection, never certify the institutional corpus.

    trusted_manifest_sha256 must be pinned outside the manifest by the reviewer.
    Even a matching digest does not authenticate what the public server returned.
    """
    result = {
        "schema": SCHEMA,
        "structural_pass": False,
        "external_digest_match": False,
        "output_reconciled": False,
        "unique_records": 0,
        "duplicate_observations": 0,
        "pages_checked": 0,
        "pagination_claim_consistent": False,
        "source_attestation_verified": False,
        "corpus_complete": False,
        "production_gate": "HOLD",
        "reasons": [],
    }
    reasons = result["reasons"]
    if not isinstance(manifest, dict) or not isinstance(pages, list):
        reasons.append("manifest_or_pages_invalid")
        return result

    # A trusted digest comes from outside the document, never manifest['sha'].
    if trusted_manifest_sha256 is not None:
        if digest_ok(trusted_manifest_sha256) and sha(manifest) == trusted_manifest_sha256:
            result["external_digest_match"] = True
        else:
            reasons.append("external_anchor_mismatch")
    else:
        reasons.append("independent_manifest_anchor_missing")

    if manifest.get("schema") != SCHEMA:
        reasons.append("unsupported_v2_schema")
    if manifest.get("source") != "czech_tv" or manifest.get("source_url") != SOURCE_URL:
        reasons.append("unexpected_official_source")
    scope = manifest.get("scope")
    if not isinstance(scope, dict):
        scope = {}
    if scope.get("kind") not in ("bounded_public_selection", "full_public_catalogue"):
        reasons.append("scope_not_defined")
    if not official_url(scope.get("index_url")):
        reasons.append("scope_index_url_not_official")
    if not isinstance(scope.get("definition"), str) or len(scope["definition"].strip()) < 12:
        reasons.append("scope_definition_absent")
    declared = scope.get("declared_total")
    if not natural(declared, positive=True):
        reasons.append("source_total_not_declared")
    if not digest_ok(scope.get("source_total_response_sha256")):
        reasons.append("official_total_response_digest_missing")
    if manifest.get("media_downloaded") is not False or manifest.get("production_writes") is not False:
        reasons.append("metadata_only_contract_violated")
    if manifest.get("collection_complete") is not True:
        reasons.append("collection_not_claimed_terminal")
    if manifest.get("failed_pages") != 0 or type(manifest.get("failed_pages")) is not int:
        reasons.append("failed_page_count_not_zero")

    page_count = manifest.get("page_count")
    if (not natural(page_count, positive=True) or page_count > MAX_PAGES
            or len(pages) > MAX_PAGES or page_count != len(pages)):
        reasons.append("page_count_incomplete_or_over_limit")
    if not pages:
        reasons.append("no_page_checkpoints")

    previous = GENESIS
    observed = set()
    observed_page_urls = set()
    duplicates = 0
    valid_chain = True
    valid_pagination = True
    for index, page in enumerate(pages[:MAX_PAGES]):
        if not isinstance(page, dict) or set(page) != PAGE_FIELDS:
            reasons.append("page_checkpoint_schema_invalid")
            valid_chain = False
            valid_pagination = False
            break
        result["pages_checked"] += 1
        payload = {k: v for k, v in page.items()
                   if k not in ("previous_chain_sha256", "chain_sha256")}
        if (page["previous_chain_sha256"] != previous
                or page["chain_sha256"] != hashlib.sha256(
                    (previous + canonical(payload)).encode("utf-8")
                ).hexdigest()):
            reasons.append("checkpoint_chain_tampered")
            valid_chain = False
            break
        previous = page["chain_sha256"]

        if page["page_index"] != index or type(page["page_index"]) is not int:
            reasons.append("missing_or_reordered_page")
            valid_pagination = False
        if not official_url(page["page_url"]):
            reasons.append("page_url_not_official")
            valid_pagination = False
        elif page["page_url"] in observed_page_urls:
            reasons.append("duplicate_page_url")
            valid_pagination = False
        else:
            observed_page_urls.add(page["page_url"])
        if not digest_ok(page["response_sha256"]):
            reasons.append("page_response_digest_invalid")
            valid_pagination = False
        if page["http_status"] != 200 or type(page["http_status"]) is not int or page["error"] is not None:
            reasons.append("page_request_failed")
            valid_pagination = False
        if page["declared_total"] != declared or type(page["declared_total"]) is not int:
            reasons.append("page_total_inconsistent")
            valid_pagination = False
        ids = page["record_ids"]
        if (not isinstance(ids, list) or not 1 <= len(ids) <= MAX_RECORDS_PER_PAGE
                or any(not isinstance(v, str) or not ID.fullmatch(v) for v in ids)):
            reasons.append("page_record_ids_invalid")
            valid_pagination = False
        else:
            if len(set(ids)) != len(ids):
                reasons.append("intra_page_duplicate_ids")
                valid_pagination = False
            duplicates += len(set(ids) & observed)
            observed.update(ids)

        last = index == len(pages) - 1
        if last:
            if (page["terminal"] is not True or page["next_page_index"] is not None
                    or page["terminal_reason"] != "official_next_page_absent"):
                reasons.append("terminal_pagination_not_documented")
                valid_pagination = False
        elif (page["terminal"] is not False
              or page["terminal_reason"] is not None
              or page["next_page_index"] != index + 1
              or type(page["next_page_index"]) is not int):
            reasons.append("pagination_link_broken")
            valid_pagination = False

    result["unique_records"] = len(observed)
    result["duplicate_observations"] = duplicates
    result["pagination_claim_consistent"] = valid_pagination and valid_chain and bool(pages)
    if manifest.get("checkpoint_chain_sha256") != previous or not valid_chain:
        reasons.append("manifest_chain_root_mismatch")
    if manifest.get("unique_record_ids_sha256") != sha(sorted(observed)):
        reasons.append("deduplicated_record_digest_mismatch")
    if manifest.get("unique_records") != len(observed) or type(manifest.get("unique_records")) is not int:
        reasons.append("unique_count_inconsistent")
    if manifest.get("duplicate_observations") != duplicates or type(manifest.get("duplicate_observations")) is not int:
        reasons.append("deduplication_count_inconsistent")
    if declared != len(observed):
        reasons.append("official_declared_total_not_reconciled")

    if output_urls is not None:
        if (not isinstance(output_urls, list) or not output_urls
                or any(not official_url(url, episode=True) for url in output_urls)):
            reasons.append("output_urls_invalid")
        else:
            exported = [EPISODE_PATH.fullmatch(urlparse(url).path).group(1) for url in output_urls]
            if len(set(exported)) != len(exported) or set(exported) != observed:
                reasons.append("output_not_reconciled_with_manifest")
            else:
                result["output_reconciled"] = True
    else:
        reasons.append("independent_output_reconciliation_missing")

    # All flags above are self-contained consistency checks. They are not
    # source provenance or authorization to crawl the rest of the catalogue.
    integrity_reasons = [v for v in reasons if v not in (
        "independent_manifest_anchor_missing",
        "independent_output_reconciliation_missing",
    )]
    result["structural_pass"] = not integrity_reasons and valid_chain and valid_pagination
    reasons.append("official_live_pagination_not_independently_attested")
    reasons.append("production_gate_p0_and_scope_review_required")
    return result


def main():
    parser = argparse.ArgumentParser(description="Offline Czech TV v2 audit (production HOLD)")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    parser.add_argument("--trusted-sha256", default=None)
    parser.add_argument("--offline-only", action="store_true",
                        help="Return 0 for consistent offline evidence only; never production admission")
    parser.add_argument("--output-urls", type=Path, default=None,
                        help="JSON list of public episode URLs, not stream URLs")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        pages = json.loads(args.pages.read_text(encoding="utf-8"))
        urls = json.loads(args.output_urls.read_text(encoding="utf-8")) if args.output_urls else None
        result = audit(manifest, pages, trusted_manifest_sha256=args.trusted_sha256,
                       output_urls=urls)
    except (OSError, ValueError, TypeError) as error:
        result = {"production_gate": "HOLD", "structural_pass": False,
                  "reasons": ["evidence_unreadable_" + type(error).__name__]}
    print(canonical(result))
    # Default command is a production-facing HOLD. Offline verification must
    # be explicitly requested and must never change production_gate.
    return 0 if (
        args.offline_only and result.get("structural_pass")
        and result.get("external_digest_match") and result.get("output_reconciled")
    ) else 2


if __name__ == "__main__":
    raise SystemExit(main())
