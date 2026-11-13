"""Synthetic-only Czech TV capture receipts: access claims vs independent evidence."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import unittest

from scripts.czech_capture_receipts import (
    SCHEMA, MAX_BODY_BYTES, audit_receipt, capture_receipt, canonical,
)


INDEX = "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/?page=0"
ID = "226544160470030"
REV = "a" * 40
BODY = b'<html><script id="__NEXT_DATA__">{"synthetic":true}</script></html>'


def fixture(**overrides):
    values = dict(
        page_index=0, requested_url=INDEX, final_url=INDEX,
        http_status=200, response_body=BODY,
        captured_at=datetime(2026, 11, 11, 18, 0, tzinfo=timezone.utc),
        content_type="text/html", declared_total=1, record_ids=[ID],
        terminal=True, next_page_index=None, code_revision=REV,
    )
    values.update(overrides)
    return capture_receipt(**values)


def pin(receipt):
    return hashlib.sha256(canonical(receipt).encode("utf-8")).hexdigest()


class CzechCaptureReceiptTests(unittest.TestCase):
    def test_valid_receipt_is_unattested_even_after_digest_replay(self):
        receipt = fixture()
        result = audit_receipt(receipt, independently_pinned_sha256=pin(receipt), raw_body=BODY)
        self.assertTrue(result["receipt_integrity_ok"])
        self.assertTrue(result["external_anchor_match"])
        self.assertTrue(result["body_digest_replayed"])
        self.assertFalse(result["source_attested"])
        self.assertFalse(result["corpus_complete"])
        self.assertEqual(result["production_gate"], "HOLD")
        encoded = canonical(receipt)
        self.assertNotIn("synthetic", encoded)
        self.assertEqual(receipt["response"]["byte_count"], len(BODY))
        self.assertEqual(receipt["schema"], SCHEMA)

    def test_tampering_after_external_pin_is_detected(self):
        receipt = fixture()
        trusted_pin = pin(receipt)
        receipt["page"]["record_ids_claim"] = ["226544160470031"]
        result = audit_receipt(receipt, independently_pinned_sha256=trusted_pin, raw_body=BODY)
        self.assertTrue(result["receipt_integrity_ok"])
        self.assertFalse(result["external_anchor_match"])
        self.assertEqual(result["production_gate"], "HOLD")

    def test_modified_body_is_detected_when_replayed(self):
        receipt = fixture()
        result = audit_receipt(
            receipt, independently_pinned_sha256=pin(receipt),
            raw_body=BODY + b"altered",
        )
        self.assertFalse(result["body_digest_replayed"])
        self.assertIn("body_digest_mismatch", result["reasons"])

    def test_hash_only_does_not_prove_original_response(self):
        receipt = fixture()
        result = audit_receipt(receipt, independently_pinned_sha256=pin(receipt))
        self.assertTrue(result["external_anchor_match"])
        self.assertFalse(result["body_digest_replayed"])
        self.assertIn("raw_body_not_available_for_independent_replay", result["reasons"])

    def test_source_official_url_rejects_credentials_redirect_and_token_query(self):
        invalid = [
            "http://www.ceskatelevize.cz/ivysilani/",
            "https://malicious.example/ivysilani/",
            "https://user:password@www.ceskatelevize.cz/ivysilani/",
            INDEX + "&token=secret",
            INDEX + "#fragment",
        ]
        for url in invalid:
            with self.subTest(url=url), self.assertRaises(ValueError):
                fixture(requested_url=url, final_url=url)
        with self.assertRaises(ValueError):
            fixture(final_url="https://www.ceskatelevize.cz/ivysilani/")

    def test_http_errors_and_oversized_or_empty_body_block(self):
        with self.assertRaises(ValueError):
            fixture(http_status=403)
        with self.assertRaises(ValueError):
            fixture(http_status=True)
        with self.assertRaises(ValueError):
            fixture(response_body=b"")
        with self.assertRaises(ValueError):
            fixture(response_body=b"x" * (MAX_BODY_BYTES + 1))
        with self.assertRaises(ValueError):
            fixture(response_body="<html>not bytes</html>")

    def test_terminal_claim_requires_no_next_and_nonterminal_requires_consecutive_index(self):
        with self.assertRaises(ValueError):
            fixture(next_page_index=1)
        with self.assertRaises(ValueError):
            fixture(terminal=False, next_page_index=None)
        with self.assertRaises(ValueError):
            fixture(terminal=False, next_page_index=5)
        record = fixture(terminal=False, next_page_index=1)
        self.assertEqual(record["page"]["next_page_index_claim"], 1)
        self.assertFalse(record["page"]["terminal_claim"])

    def test_page_id_validation_requires_public_numeric_unique_identifiers(self):
        for ids in [[ID, ID], ["private"], ["abc"], [], [ID, "not-a-id"]]:
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                fixture(record_ids=ids)

    def test_boolean_page_counters_rejected(self):
        for kwargs in ({"page_index": True}, {"declared_total": True}, {"terminal": 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                fixture(**kwargs)

    def test_time_requires_timezone_and_is_normalized_to_utc(self):
        with self.assertRaises(ValueError):
            fixture(captured_at=datetime(2026, 11, 11, 18))
        record = fixture(captured_at=datetime(
            2026, 11, 11, 15, tzinfo=timezone(timedelta(hours=-3))))
        self.assertEqual(record["captured_at_utc"], "2026-11-11T18:00:00Z")

    def test_spoofed_successful_production_claim_is_rejected(self):
        receipt = fixture()
        receipt["source_attested"] = True
        receipt["corpus_complete"] = True
        receipt["production_gate"] = "COMPLETE_VERIFIED"
        result = audit_receipt(
            receipt, independently_pinned_sha256=pin(receipt), raw_body=BODY
        )
        self.assertFalse(result["receipt_integrity_ok"])
        self.assertEqual(result["production_gate"], "HOLD")

    def test_additional_unexpected_fields_fail_closed(self):
        receipt = fixture()
        receipt["private_stream_url"] = "https://example.invalid/video"
        result = audit_receipt(receipt, independently_pinned_sha256=pin(receipt), raw_body=BODY)
        self.assertFalse(result["receipt_integrity_ok"])

    def test_response_digest_and_code_revision_required(self):
        receipt = fixture()
        receipt["response"]["body_sha256"] = "not-a-hash"
        self.assertFalse(audit_receipt(receipt)["receipt_integrity_ok"])
        with self.assertRaises(ValueError):
            fixture(code_revision="short")

    def test_synthetic_bytes_not_persisted(self):
        sensitive = b'<html>api_token=SENSITIVE-TEST-VALUE</html>'
        receipt = fixture(response_body=sensitive)
        encoded = json.dumps(receipt)
        self.assertNotIn("SENSITIVE-TEST-VALUE", encoded)
        self.assertFalse(receipt["raw_response_persisted"])


if __name__ == "__main__":
    unittest.main()
