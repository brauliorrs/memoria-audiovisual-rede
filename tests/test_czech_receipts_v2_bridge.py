"""Deterministic bridge regression: synthetic public episode HTML only."""
from datetime import datetime, timezone
import hashlib
import unittest

from scripts.audit_czech_completeness_v2 import (
    GENESIS, SCHEMA, SOURCE_URL, checkpoint, sha,
)
from scripts.czech_capture_receipts import capture_receipt, canonical
from scripts.replay_czech_receipts_v2 import replay_receipts_to_v2

BASE = "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/?page="
SHOW = "12701251153-kultura"
IDS = ("226544160470030", "226544160470031", "226544160470032")
COMMIT = "a" * 40


def source_fixture():
    """Two page HTML specimen, not a real official Czech TV response."""
    a, b, c = IDS
    bodies = [
        (f'<html><head><link rel="next" href="?page=1"></head>'
         f'<body><a href="/porady/{SHOW}/{a}/">A</a>'
         f'<a href="/porady/{SHOW}/{b}/">B</a></body></html>').encode(),
        (f'<html><body><a href="/porady/{SHOW}/{b}/">B</a>'
         f'<a href="/porady/{SHOW}/{c}/">C</a></body></html>').encode(),
    ]
    receipts = []
    for index, ids in enumerate([IDS[:2], IDS[1:]]):
        receipts.append(capture_receipt(
            page_index=index, requested_url=BASE + str(index),
            final_url=BASE + str(index), http_status=200,
            response_body=bodies[index],
            captured_at=datetime(2026, 11, 11, 20, 0, tzinfo=timezone.utc),
            content_type="text/html", declared_total=3, record_ids=list(ids),
            terminal=index == 1, next_page_index=None if index == 1 else 1,
            code_revision=COMMIT,
        ))
    pins = [hashlib.sha256(canonical(item).encode("utf-8")).hexdigest()
            for item in receipts]
    previous = GENESIS
    pages = []
    for i, receipt in enumerate(receipts):
        payload = receipt["page"]
        page = checkpoint({
            "page_index": i, "page_url": receipt["request"]["url"],
            "response_sha256": receipt["response"]["body_sha256"],
            "declared_total": payload["declared_total_claim"],
            "record_ids": payload["record_ids_claim"],
            "terminal": payload["terminal_claim"],
            "terminal_reason": "official_next_page_absent" if i == 1 else None,
            "next_page_index": payload["next_page_index_claim"],
            "http_status": 200, "error": None,
        }, previous)
        pages.append(page)
        previous = page["chain_sha256"]
    manifest = {
        "schema": SCHEMA,
        "source": "czech_tv",
        "source_url": SOURCE_URL,
        "scope": {
            "kind": "bounded_public_selection",
            "definition": "Only a synthetic two-page fixture for offline unit tests.",
            "index_url": BASE + "0",
            "declared_total": 3,
            "source_total_response_sha256": "c" * 64,
        },
        "page_count": 2, "failed_pages": 0,
        "unique_records": 3, "duplicate_observations": 1,
        "unique_record_ids_sha256": sha(sorted(IDS)),
        "checkpoint_chain_sha256": pages[-1]["chain_sha256"],
        "collection_complete": True,
        "media_downloaded": False, "production_writes": False,
    }
    outputs = [f"https://www.ceskatelevize.cz/porady/{SHOW}/{id}/" for id in IDS]
    return receipts, bodies, pins, manifest, sha(manifest), outputs


def evaluate(*, receipts=None, bodies=None, pins=None, manifest=None,
             manifest_pin=None, outputs=None):
    baseline = source_fixture()
    return replay_receipts_to_v2(
        receipts=baseline[0] if receipts is None else receipts,
        bodies=baseline[1] if bodies is None else bodies,
        receipt_sha256_pins=baseline[2] if pins is None else pins,
        manifest=baseline[3] if manifest is None else manifest,
        manifest_sha256_pin=baseline[4] if manifest_pin is None else manifest_pin,
        output_urls=baseline[5] if outputs is None else outputs,
    )


class CzechReceiptV2BridgeTests(unittest.TestCase):
    def test_replayed_html_matches_receipts_and_v2_but_never_production(self):
        result = evaluate()
        self.assertTrue(result["bridge_replay_consistent"])
        self.assertEqual(result["receipt_replay_count"], 2)
        self.assertEqual(result["reextracted_unique_records"], 3)
        self.assertTrue(result["v2_structural_pass"])
        self.assertTrue(result["v2_manifest_anchor_match"])
        self.assertTrue(result["v2_output_reconciled"])
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["official_total_attested"])
        self.assertFalse(result["terminal_exhaustion_attested"])
        self.assertFalse(result["raw_response_persisted"])
        self.assertFalse(result["corpus_complete"])
        self.assertEqual(result["production_gate"], "HOLD")

    def test_claimed_ids_differing_from_reparsed_html_are_rejected(self):
        receipts, bodies, pins, manifest, manifest_pin, outputs = source_fixture()
        receipts[0]["page"]["record_ids_claim"] = [IDS[0], IDS[2]]
        pins[0] = hashlib.sha256(canonical(receipts[0]).encode()).hexdigest()
        result = evaluate(receipts=receipts, bodies=bodies, pins=pins,
                          manifest=manifest, manifest_pin=manifest_pin, outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("claimed_ids_differ_from_reextracted_html", result["reasons"])

    def test_wrong_receipt_pin_blocks_even_when_body_matches(self):
        pins = source_fixture()[2]
        pins[0] = "0" * 64
        result = evaluate(pins=pins)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("receipt_unverifiable_at_index_0", result["reasons"])

    def test_edited_response_body_blocks(self):
        bodies = source_fixture()[1]
        bodies[1] += b"changed"
        result = evaluate(bodies=bodies)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("receipt_unverifiable_at_index_1", result["reasons"])

    def test_swapped_bodies_are_rejected(self):
        bodies = source_fixture()[1]
        bodies.reverse()
        self.assertFalse(evaluate(bodies=bodies)["bridge_replay_consistent"])

    def test_absent_second_page_is_rejected(self):
        receipts, bodies, pins, _, _, _ = source_fixture()
        result = evaluate(receipts=receipts[:1], bodies=bodies[:1], pins=pins[:1])
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("next_page_link_does_not_match_following_receipt", result["reasons"])

    def test_missing_next_link_blocks_claimed_nonterminal_page(self):
        receipts, bodies, pins, manifest, manifest_pin, outputs = source_fixture()
        bodies[0] = bodies[0].replace(b'<link rel="next" href="?page=1">', b"")
        receipts[0]["response"]["body_sha256"] = hashlib.sha256(bodies[0]).hexdigest()
        receipts[0]["response"]["byte_count"] = len(bodies[0])
        pins[0] = hashlib.sha256(canonical(receipts[0]).encode()).hexdigest()
        result = evaluate(receipts=receipts, bodies=bodies, pins=pins,
                          manifest=manifest, manifest_pin=manifest_pin, outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("next_page_link_not_independently_observed", result["reasons"])

    def test_terminal_page_with_next_link_is_rejected(self):
        receipts, bodies, pins, manifest, manifest_pin, outputs = source_fixture()
        bodies[1] = bodies[1].replace(b"<head>", b'<head><link rel="next" href="?page=2">') \
            if b"<head>" in bodies[1] else bodies[1].replace(
                b"<body>", b'<head><link rel="next" href="?page=2"></head><body>')
        receipts[1]["response"]["body_sha256"] = hashlib.sha256(bodies[1]).hexdigest()
        receipts[1]["response"]["byte_count"] = len(bodies[1])
        pins[1] = hashlib.sha256(canonical(receipts[1]).encode()).hexdigest()
        result = evaluate(receipts=receipts, bodies=bodies, pins=pins,
                          manifest=manifest, manifest_pin=manifest_pin, outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("terminal_claim_contradicted_by_next_link", result["reasons"])

    def test_unrecognized_foreign_domain_link_does_not_become_evidence(self):
        receipts, bodies, pins, manifest, manifest_pin, outputs = source_fixture()
        bodies[0] = bodies[0].replace(
            b"</body>", b'<a href="https://evil.example/porady/12701251153-kultura/12345678/">Foreign</a></body>'
        )
        receipts[0]["response"]["body_sha256"] = hashlib.sha256(bodies[0]).hexdigest()
        receipts[0]["response"]["byte_count"] = len(bodies[0])
        pins[0] = hashlib.sha256(canonical(receipts[0]).encode()).hexdigest()
        # The content hash changes, so the independently pinned v2 manifest
        # cannot match the derived checkpoint; this must remain HOLD.
        result = evaluate(receipts=receipts, bodies=bodies, pins=pins,
                          manifest=manifest, manifest_pin=manifest_pin, outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertFalse(result["v2_structural_pass"])

    def test_wrong_manifest_anchor_blocks_replay(self):
        result = evaluate(manifest_pin="0" * 64)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertFalse(result["v2_manifest_anchor_match"])

    def test_missing_exported_episode_blocks_reconciliation(self):
        outputs = source_fixture()[5][:2]
        result = evaluate(outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertFalse(result["v2_output_reconciled"])

    def test_full_corpus_claim_is_never_accepted_by_bounded_bridge(self):
        manifest = source_fixture()[3]
        manifest["scope"]["kind"] = "full_public_catalogue"
        result = evaluate(manifest=manifest, manifest_pin=sha(manifest))
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("bridge_only_supports_bounded_selection", result["reasons"])
        self.assertEqual(result["production_gate"], "HOLD")

    def test_no_episode_links_blocks_even_valid_receipt_and_pin(self):
        receipts, bodies, pins, manifest, manifest_pin, outputs = source_fixture()
        bodies[0] = b"<html><body><a href='/porady/12701251153-kultura/'>Show only</a></body></html>"
        receipts[0]["response"]["body_sha256"] = hashlib.sha256(bodies[0]).hexdigest()
        receipts[0]["response"]["byte_count"] = len(bodies[0])
        pins[0] = hashlib.sha256(canonical(receipts[0]).encode()).hexdigest()
        result = evaluate(receipts=receipts, bodies=bodies, pins=pins,
                          manifest=manifest, manifest_pin=manifest_pin, outputs=outputs)
        self.assertFalse(result["bridge_replay_consistent"])
        self.assertIn("no_public_episode_links_in_response", result["reasons"])


if __name__ == "__main__":
    unittest.main()
