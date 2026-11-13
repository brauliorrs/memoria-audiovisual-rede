"""P0 offline encrypted Czech evidence bundle: pre-production synthetic tests."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.audit_czech_completeness_v2 import (
    GENESIS, SCHEMA as V2_SCHEMA, SOURCE_URL, checkpoint, sha,
)
from scripts.czech_capture_receipts import capture_receipt, canonical
from scripts.czech_evidence_p0_offline import (
    EvidenceRejected, seal_synthetic_bundle, unseal_and_replay_synthetic_bundle,
)

BASE = "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/?page="
SHOW = "12701251153-kultura"
IDS = ("226544160470030", "226544160470031", "226544160470032")
KEY = bytes(range(32))
WRONG_KEY = b"x" * 32
REV = "a" * 40


def fixture():
    bodies = [
        (f'<html><head><link rel="next" href="?page=1"></head><body>'
         f'<a href="/porady/{SHOW}/{IDS[0]}/">One</a>'
         f'<a href="/porady/{SHOW}/{IDS[1]}/">Two</a></body></html>').encode(),
        (f'<html><body><a href="/porady/{SHOW}/{IDS[1]}/">Two</a>'
         f'<a href="/porady/{SHOW}/{IDS[2]}/">Three</a></body></html>').encode(),
    ]
    receipts = [
        capture_receipt(
            page_index=i, requested_url=BASE + str(i),
            final_url=BASE + str(i), http_status=200,
            response_body=bodies[i],
            captured_at=datetime(2026, 11, 11, 21, 0, tzinfo=timezone.utc),
            content_type="text/html", declared_total=3,
            record_ids=list(IDS[:2] if i == 0 else IDS[1:]),
            terminal=i == 1, next_page_index=None if i == 1 else 1,
            code_revision=REV,
        ) for i in range(2)
    ]
    pins = [hashlib.sha256(canonical(receipt).encode()).hexdigest()
            for receipt in receipts]
    chain = GENESIS
    for i, receipt in enumerate(receipts):
        page = receipt["page"]
        item = checkpoint({
            "page_index": i, "page_url": receipt["request"]["url"],
            "response_sha256": receipt["response"]["body_sha256"],
            "declared_total": 3,
            "record_ids": page["record_ids_claim"],
            "terminal": page["terminal_claim"],
            "terminal_reason": "official_next_page_absent" if i == 1 else None,
            "next_page_index": page["next_page_index_claim"],
            "http_status": 200, "error": None,
        }, chain)
        chain = item["chain_sha256"]
    manifest = {
        "schema": V2_SCHEMA, "source": "czech_tv",
        "source_url": SOURCE_URL,
        "scope": {
            "kind": "bounded_public_selection",
            "definition": "Synthetic two-page replay; not a complete institutional corpus.",
            "index_url": BASE + "0", "declared_total": 3,
            "source_total_response_sha256": "c" * 64,
        },
        "page_count": 2, "failed_pages": 0,
        "unique_records": 3, "duplicate_observations": 1,
        "unique_record_ids_sha256": sha(sorted(IDS)),
        "checkpoint_chain_sha256": chain,
        "collection_complete": True,
        "media_downloaded": False, "production_writes": False,
    }
    return dict(
        receipts=receipts, bodies=bodies, receipt_pins=pins,
        manifest=manifest, manifest_pin=sha(manifest),
        output_urls=[f"https://www.ceskatelevize.cz/porady/{SHOW}/{id}/" for id in IDS],
        scope_id="czech-synthetic-two-pages", key=KEY,
    )


class CzechEvidenceP0OfflineTests(unittest.TestCase):
    def test_encrypt_and_restore_in_separate_temporary_directories(self):
        values = fixture()
        ciphertext, sealed_review = seal_synthetic_bundle(**values)
        self.assertTrue(sealed_review["offline_replay_consistent"])
        self.assertFalse(sealed_review["durability_verified"])
        self.assertFalse(sealed_review["source_attested"])
        self.assertEqual(sealed_review["production_gate"], "HOLD")
        self.assertNotIn(values["bodies"][0], ciphertext)
        self.assertNotIn(IDS[0].encode(), ciphertext)
        self.assertNotIn(values["output_urls"][0].encode(), ciphertext)
        with tempfile.TemporaryDirectory() as home:
            backup_home = Path(home) / "archive"
            restore_home = Path(home) / "restored"
            backup_home.mkdir(mode=0o700)
            restore_home.mkdir(mode=0o700)
            path = backup_home / "synthetic-bundle.enc"
            path.write_bytes(ciphertext)
            if os.name == "posix":
                path.chmod(0o600)
            read_back = path.read_bytes()
            restored, report = unseal_and_replay_synthetic_bundle(
                read_back, key=KEY,
                expected_scope_id=values["scope_id"],
                expected_manifest_pin=values["manifest_pin"],
                expected_receipt_pins=values["receipt_pins"],
                independently_pinned_encrypted_sha256=sealed_review["encrypted_sha256"],
            )
            self.assertEqual(restored["bodies"], values["bodies"])
            self.assertEqual(restored["manifest"], values["manifest"])
            self.assertEqual(report["status"], "synthetic_restored_and_replayed_in_memory")
            self.assertTrue(report["offline_replay_consistent"])
            self.assertFalse(report["durability_verified"])
            self.assertEqual(report["production_gate"], "HOLD")
            self.assertFalse(list(restore_home.iterdir()))

    def test_random_nonce_means_distinct_backups_for_same_synthetic_payload(self):
        args = fixture()
        a, _ = seal_synthetic_bundle(**args)
        b, _ = seal_synthetic_bundle(**args)
        self.assertNotEqual(a, b)

    def test_wrong_key_rejects_restore(self):
        args = fixture()
        sealed, report = seal_synthetic_bundle(**args)
        with self.assertRaises(EvidenceRejected):
            unseal_and_replay_synthetic_bundle(
                sealed, key=WRONG_KEY,
                expected_scope_id=args["scope_id"],
                expected_manifest_pin=args["manifest_pin"],
                expected_receipt_pins=args["receipt_pins"],
                independently_pinned_encrypted_sha256=report["encrypted_sha256"],
            )

    def test_wrong_scope_manifest_and_receipt_anchors_reject(self):
        args = fixture()
        sealed, report = seal_synthetic_bundle(**args)
        original = dict(
            key=KEY, expected_scope_id=args["scope_id"],
            expected_manifest_pin=args["manifest_pin"],
            expected_receipt_pins=args["receipt_pins"],
            independently_pinned_encrypted_sha256=report["encrypted_sha256"],
        )
        for change in (
            {"expected_scope_id": "different-scoped-bundle"},
            {"expected_manifest_pin": "0" * 64},
            {"expected_receipt_pins": ["0" * 64] + args["receipt_pins"][1:]},
            {"independently_pinned_encrypted_sha256": "0" * 64},
        ):
            with self.subTest(change=change), self.assertRaises(EvidenceRejected):
                unseal_and_replay_synthetic_bundle(sealed, **(original | change))

    def test_ciphertext_header_truncation_and_nonce_tampering_rejected(self):
        args = fixture()
        sealed, report = seal_synthetic_bundle(**args)
        variants = (
            sealed[:-1] + bytes([sealed[-1] ^ 1]),
            sealed[:-20],
            sealed[:12] + bytes([sealed[12] ^ 1]) + sealed[13:],
        )
        for tampered in variants:
            with self.subTest(digest=hashlib.sha256(tampered).hexdigest()):
                with self.assertRaises(EvidenceRejected):
                    unseal_and_replay_synthetic_bundle(
                        tampered, key=KEY,
                        expected_scope_id=args["scope_id"],
                        expected_manifest_pin=args["manifest_pin"],
                        expected_receipt_pins=args["receipt_pins"],
                        independently_pinned_encrypted_sha256=report["encrypted_sha256"],
                    )

    def test_no_backup_created_when_replay_does_not_match_html(self):
        args = fixture()
        args["receipts"][0]["page"]["record_ids_claim"] = [IDS[0], IDS[2]]
        args["receipt_pins"][0] = hashlib.sha256(
            canonical(args["receipts"][0]).encode()).hexdigest()
        with self.assertRaisesRegex(EvidenceRejected, "offline_replay_inconsistent"):
            seal_synthetic_bundle(**args)

    def test_only_synthetic_scope_supported(self):
        args = fixture()
        args["manifest"]["scope"]["kind"] = "full_public_catalogue"
        args["manifest_pin"] = sha(args["manifest"])
        with self.assertRaises(EvidenceRejected):
            seal_synthetic_bundle(**args)

    def test_invalid_key_and_bundle_identity_fail_closed(self):
        args = fixture()
        with self.assertRaises(EvidenceRejected):
            seal_synthetic_bundle(**(args | {"key": b"short"}))
        with self.assertRaises(EvidenceRejected):
            seal_synthetic_bundle(**(args | {"scope_id": "../public-destination"}))

    def test_plaintext_not_logged_or_written_by_library(self):
        args = fixture()
        sealed, result = seal_synthetic_bundle(**args)
        self.assertNotIn("226544160470030", json.dumps(result))
        self.assertNotIn(IDS[0].encode(), sealed)
        self.assertNotIn(b"<html>", sealed)
        self.assertFalse(result["durability_verified"])
        self.assertEqual(result["production_gate"], "HOLD")


if __name__ == "__main__":
    unittest.main()
