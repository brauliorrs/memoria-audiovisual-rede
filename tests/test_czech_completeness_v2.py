"""Offline v2 admission contract: consistency does not certify external origin."""
import copy
import unittest

from scripts.audit_czech_completeness_v2 import (
    GENESIS, SCHEMA, SOURCE_URL, audit, checkpoint, sha,
)

BASE = "https://www.ceskatelevize.cz/ivysilani/kategorie/4029-kultura/katalog/"
IDS = ("226544160470030", "226544160470031", "226544160470032")
SHOW = "12701251153-kultura"


def fixture():
    def payload(index, ids, *, terminal):
        return {
            "page_index": index,
            "page_url": BASE + f"?page={index}",
            "response_sha256": ("a" if index == 0 else "b") * 64,
            "declared_total": 3,
            "record_ids": list(ids),
            "terminal": terminal,
            "terminal_reason": "official_next_page_absent" if terminal else None,
            "next_page_index": None if terminal else index + 1,
            "http_status": 200,
            "error": None,
        }
    first = checkpoint(payload(0, IDS[:2], terminal=False))
    last = checkpoint(payload(1, IDS[1:], terminal=True), first["chain_sha256"])
    pages = [first, last]
    manifest = {
        "schema": SCHEMA,
        "source": "czech_tv",
        "source_url": SOURCE_URL,
        "scope": {
            "kind": "bounded_public_selection",
            "definition": "Offline synthetic culture-filter universe, not the full broadcaster.",
            "index_url": BASE,
            "declared_total": 3,
            "source_total_response_sha256": "c" * 64,
        },
        "page_count": len(pages),
        "failed_pages": 0,
        "unique_records": 3,
        "duplicate_observations": 1,
        "unique_record_ids_sha256": sha(sorted(IDS)),
        "checkpoint_chain_sha256": last["chain_sha256"],
        "collection_complete": True,
        "media_downloaded": False,
        "production_writes": False,
    }
    outputs = [
        f"https://www.ceskatelevize.cz/porady/{SHOW}/{identifier}/"
        for identifier in IDS
    ]
    return manifest, pages, outputs


def verified(manifest, pages, output_urls):
    return audit(manifest, pages, trusted_manifest_sha256=sha(manifest),
                 output_urls=output_urls)


class CzechV2OfflineEvidenceTests(unittest.TestCase):
    def test_synthetic_bounded_corpus_is_structurally_consistent_but_production_hold(self):
        manifest, pages, outputs = fixture()
        result = verified(manifest, pages, outputs)
        self.assertTrue(result["structural_pass"])
        self.assertTrue(result["external_digest_match"])
        self.assertTrue(result["output_reconciled"])
        self.assertTrue(result["pagination_claim_consistent"])
        self.assertEqual(result["unique_records"], 3)
        self.assertEqual(result["duplicate_observations"], 1)
        self.assertEqual(result["pages_checked"], 2)
        self.assertEqual(result["production_gate"], "HOLD")
        self.assertFalse(result["corpus_complete"])
        self.assertFalse(result["source_attestation_verified"])

    def test_missing_second_page_is_detected(self):
        manifest, pages, outputs = fixture()
        result = verified(manifest, pages[:1], outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("page_count_incomplete_or_over_limit", result["reasons"])
        self.assertIn("terminal_pagination_not_documented", result["reasons"])

    def test_changed_record_ids_without_chain_recalculation_fails(self):
        manifest, pages, outputs = fixture()
        pages[1]["record_ids"] = [IDS[0]]
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("checkpoint_chain_tampered", result["reasons"])

    def test_changed_terminal_with_recalculated_chain_fails_external_anchor(self):
        manifest, pages, outputs = fixture()
        pinned = sha(manifest)
        bad_final = copy.deepcopy(pages[1])
        bad_final["terminal_reason"] = None
        bad_final.pop("previous_chain_sha256")
        bad_final.pop("chain_sha256")
        pages[1] = checkpoint(bad_final, pages[0]["chain_sha256"])
        manifest["checkpoint_chain_sha256"] = pages[1]["chain_sha256"]
        result = audit(manifest, pages, trusted_manifest_sha256=pinned,
                       output_urls=outputs)
        self.assertFalse(result["structural_pass"])
        self.assertFalse(result["external_digest_match"])
        self.assertIn("external_anchor_mismatch", result["reasons"])
        self.assertIn("terminal_pagination_not_documented", result["reasons"])

    def test_page_gap_and_broken_next_pointer_are_rejected(self):
        manifest, pages, outputs = fixture()
        invalid = copy.deepcopy(pages[0])
        invalid["next_page_index"] = 99
        invalid.pop("previous_chain_sha256")
        invalid.pop("chain_sha256")
        pages[0] = checkpoint(invalid)
        last = copy.deepcopy(pages[1])
        last["page_index"] = 3
        last.pop("previous_chain_sha256")
        last.pop("chain_sha256")
        pages[1] = checkpoint(last, pages[0]["chain_sha256"])
        manifest["checkpoint_chain_sha256"] = pages[-1]["chain_sha256"]
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("pagination_link_broken", result["reasons"])
        self.assertIn("missing_or_reordered_page", result["reasons"])

    def test_repeated_official_page_url_cannot_prove_full_pagination(self):
        manifest, pages, outputs = fixture()
        second = copy.deepcopy(pages[1])
        second["page_url"] = pages[0]["page_url"]
        second.pop("previous_chain_sha256")
        second.pop("chain_sha256")
        pages[1] = checkpoint(second, pages[0]["chain_sha256"])
        manifest["checkpoint_chain_sha256"] = pages[-1]["chain_sha256"]
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("duplicate_page_url", result["reasons"])

    def test_duplicate_episode_record_in_same_page_fails(self):
        manifest, pages, outputs = fixture()
        last = copy.deepcopy(pages[1])
        last["record_ids"] = [IDS[1], IDS[1], IDS[2]]
        last.pop("previous_chain_sha256")
        last.pop("chain_sha256")
        pages[1] = checkpoint(last, pages[0]["chain_sha256"])
        manifest["checkpoint_chain_sha256"] = pages[-1]["chain_sha256"]
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("intra_page_duplicate_ids", result["reasons"])

    def test_mismatched_declared_total_and_dedup_count_fails(self):
        manifest, pages, outputs = fixture()
        manifest["scope"]["declared_total"] = 5
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("official_declared_total_not_reconciled", result["reasons"])

    def test_duplicate_export_link_is_rejected(self):
        manifest, pages, outputs = fixture()
        outputs[1] = outputs[0]
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["output_reconciled"])
        self.assertFalse(result["structural_pass"])
        self.assertIn("output_not_reconciled_with_manifest", result["reasons"])

    def test_missing_external_digest_and_outputs_do_not_promote(self):
        manifest, pages, _ = fixture()
        result = audit(manifest, pages)
        self.assertTrue(result["structural_pass"])
        self.assertFalse(result["external_digest_match"])
        self.assertFalse(result["output_reconciled"])
        self.assertEqual(result["production_gate"], "HOLD")
        self.assertIn("independent_manifest_anchor_missing", result["reasons"])

    def test_cross_domain_episode_export_is_rejected(self):
        manifest, pages, outputs = fixture()
        outputs[0] = "https://evil.example/porady/12701251153-kultura/226544160470030/"
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("output_urls_invalid", result["reasons"])

    def test_http_error_or_nonzero_failed_pages_blocks(self):
        manifest, pages, outputs = fixture()
        manifest["failed_pages"] = 1
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("failed_page_count_not_zero", result["reasons"])

    def test_full_source_scope_cannot_be_promoted_by_fabricated_self_reports(self):
        manifest, pages, outputs = fixture()
        manifest["scope"]["kind"] = "full_public_catalogue"
        result = verified(manifest, pages, outputs)
        self.assertTrue(result["structural_pass"])
        self.assertFalse(result["corpus_complete"])
        self.assertEqual(result["production_gate"], "HOLD")
        self.assertIn("official_live_pagination_not_independently_attested", result["reasons"])

    def test_boolean_counts_are_not_accepted(self):
        manifest, pages, outputs = fixture()
        manifest["page_count"] = True
        manifest["unique_records"] = True
        result = verified(manifest, pages, outputs)
        self.assertFalse(result["structural_pass"])
        self.assertIn("page_count_incomplete_or_over_limit", result["reasons"])
        self.assertIn("unique_count_inconsistent", result["reasons"])


if __name__ == "__main__":
    unittest.main()
