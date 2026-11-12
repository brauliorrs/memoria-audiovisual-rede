"""Replay Czech capture receipts into the v2 completeness auditor (offline only).

This bridge receives *supplied* HTML bytes, independent receipt SHA pins,
a separately pinned v2 manifest and exported public episode URLs.
No HTTP access, no filesystem persistence, no video or production mutation.

Replay proves agreement between bytes, receipt claims, extracted episode links
and v2 checkpoints. It CANNOT prove those bytes were served by Czech Television
or that the source's official universe has been exhausted.
"""
from __future__ import annotations

from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from scripts.audit_czech_completeness_v2 import (
    EPISODE_PATH, GENESIS, audit as audit_v2, checkpoint, official_url,
)
from scripts.czech_capture_receipts import audit_receipt, _url_allowed

MAX_PAGES_TO_REPLAY = 20


class _EpisodeLinkReader(HTMLParser):
    """Independent bounded HTML link interpretation, not the collector parser."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.episode_hrefs = []
        self.next_hrefs = []

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        href = values.get("href")
        if not isinstance(href, str):
            return
        if tag == "a":
            self.episode_hrefs.append(href)
        if tag in ("link", "a"):
            rel = values.get("rel")
            if isinstance(rel, str) and "next" in rel.lower().split():
                self.next_hrefs.append(href)


def _extract_links(body, page_url):
    """Extract only institutional episode links from supplied HTML."""
    if not isinstance(body, bytes) or not 1 <= len(body) <= 512 * 1024:
        raise ValueError("missing_or_oversized_response_bytes")
    try:
        html = body.decode("utf-8", "strict")
    except UnicodeDecodeError as error:
        raise ValueError("html_not_utf8") from error
    parser = _EpisodeLinkReader()
    parser.feed(html)
    parser.close()
    identifiers = []
    public_urls = {}
    for href in parser.episode_hrefs:
        url = urljoin(page_url, href)
        if not official_url(url, episode=True):
            continue
        identifier = EPISODE_PATH.fullmatch(urlparse(url).path).group(1)
        if identifier not in public_urls:
            public_urls[identifier] = url
            identifiers.append(identifier)
    next_urls = [urljoin(page_url, href) for href in parser.next_hrefs]
    return identifiers, public_urls, next_urls


def replay_receipts_to_v2(
    *, receipts, bodies, receipt_sha256_pins, manifest,
    manifest_sha256_pin, output_urls,
):
    """Cross-check receipts and re-extracted IDs against a separately pinned v2.

    All inputs are supplied by the caller (e.g. synthetic tests). Each
    positive outcome is only an offline consistency claim; even a perfect
    fixture stays production HOLD.
    """
    result = {
        "bridge_replay_consistent": False,
        "receipt_replay_count": 0,
        "reextracted_unique_records": 0,
        "v2_structural_pass": False,
        "v2_manifest_anchor_match": False,
        "v2_output_reconciled": False,
        "source_attested": False,
        "official_total_attested": False,
        "terminal_exhaustion_attested": False,
        "raw_response_persisted": False,
        "corpus_complete": False,
        "production_gate": "HOLD",
        "reasons": [],
    }
    reasons = result["reasons"]
    if (
        not isinstance(receipts, list) or not isinstance(bodies, list)
        or not isinstance(receipt_sha256_pins, list)
        or not 1 <= len(receipts) <= MAX_PAGES_TO_REPLAY
        or len(receipts) != len(bodies)
        or len(receipts) != len(receipt_sha256_pins)
        or not isinstance(output_urls, list)
    ):
        reasons.append("missing_or_inconsistent_replay_inputs")
        return result

    pages = []
    seen_page_urls = set()
    previous = GENESIS
    all_ids = set()
    for index, (receipt, raw_body, pin) in enumerate(
        zip(receipts, bodies, receipt_sha256_pins)
    ):
        receipt_status = audit_receipt(
            receipt, independently_pinned_sha256=pin, raw_body=raw_body
        )
        if not all(receipt_status[key] for key in (
            "receipt_integrity_ok", "external_anchor_match", "body_digest_replayed"
        )):
            reasons.append("receipt_unverifiable_at_index_" + str(index))
            return result
        result["receipt_replay_count"] += 1
        req = receipt["request"]
        meta = receipt["page"]
        url = req["url"]
        if not _url_allowed(url) or url in seen_page_urls:
            reasons.append("duplicate_or_invalid_page_url")
            return result
        seen_page_urls.add(url)
        if meta["page_index"] != index:
            reasons.append("page_sequence_mismatch")
            return result
        if receipt["response"]["content_type"] != "text/html":
            reasons.append("html_replay_required")
            return result

        try:
            extracted_ids, _, next_urls = _extract_links(raw_body, url)
        except ValueError as error:
            reasons.append(str(error))
            return result
        if not extracted_ids:
            reasons.append("no_public_episode_links_in_response")
            return result
        if set(extracted_ids) != set(meta["record_ids_claim"]):
            reasons.append("claimed_ids_differ_from_reextracted_html")
            return result
        all_ids.update(extracted_ids)

        terminal = meta["terminal_claim"]
        if terminal:
            if next_urls:
                reasons.append("terminal_claim_contradicted_by_next_link")
                return result
        else:
            if len(next_urls) != 1 or not _url_allowed(next_urls[0]):
                reasons.append("next_page_link_not_independently_observed")
                return result
            if index + 1 >= len(receipts) or next_urls[0] != receipts[index + 1]["request"]["url"]:
                reasons.append("next_page_link_does_not_match_following_receipt")
                return result

        page = checkpoint({
            "page_index": index,
            "page_url": url,
            "response_sha256": receipt["response"]["body_sha256"],
            "declared_total": meta["declared_total_claim"],
            "record_ids": extracted_ids,
            "terminal": terminal,
            "terminal_reason": "official_next_page_absent" if terminal else None,
            "next_page_index": meta["next_page_index_claim"],
            "http_status": receipt["response"]["http_status"],
            "error": None,
        }, previous)
        pages.append(page)
        previous = page["chain_sha256"]

    result["reextracted_unique_records"] = len(all_ids)
    # The absence of a rel=next element DOES NOT prove terminal exhaustion;
    # the declared total likewise cannot be authenticated from this parser.
    # A source-specific independently proven pagination contract is pending.
    if not isinstance(manifest, dict) or manifest.get("scope", {}).get("kind") != "bounded_public_selection":
        reasons.append("bridge_only_supports_bounded_selection")
        return result
    review = audit_v2(
        manifest, pages, trusted_manifest_sha256=manifest_sha256_pin,
        output_urls=output_urls,
    )
    result["v2_structural_pass"] = review["structural_pass"]
    result["v2_manifest_anchor_match"] = review["external_digest_match"]
    result["v2_output_reconciled"] = review["output_reconciled"]
    if not all((
        result["v2_structural_pass"],
        result["v2_manifest_anchor_match"],
        result["v2_output_reconciled"],
    )):
        reasons.extend("v2:" + reason for reason in review["reasons"])
        return result
    result["bridge_replay_consistent"] = True
    reasons.append("official_capture_origin_not_attested")
    reasons.append("source_declared_total_and_terminal_not_independently_verified")
    reasons.append("p0_durable_evidence_and_production_gate_pending")
    return result
