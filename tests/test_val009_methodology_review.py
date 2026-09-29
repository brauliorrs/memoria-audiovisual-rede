"""Synthetic tests for VAL-009's documentary methodology HOLD.

No independent human judgment or new site collection is simulated as real.
An exact historical checkout is separately verified in the quality workflow.
"""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "scripts"))
import review_val009_methodology as method  # noqa: E402
from audit_val009_exposure import AuditError  # noqa: E402

INV_PATH = BASE / method.INVENTORY_FILE
REVIEW_PATH = BASE / method.REVIEW_FILE
INV_BYTES = INV_PATH.read_bytes()
INVENTORY = json.loads(INV_BYTES)
REVIEW = json.loads(REVIEW_PATH.read_bytes())


class MethodologyScreeningTests(unittest.TestCase):
    def checked(self, candidate=None, inventory=INVENTORY, raw=INV_BYTES):
        return method.validate_methodology_structure(
            REVIEW if candidate is None else candidate, inventory, raw
        )

    def test_documentary_screening_keeps_scientific_gate_closed(self):
        result = self.checked()
        self.assertEqual(result["proven_historical_urls"], 137)
        self.assertEqual(result["test_literals_screened"], 22)
        self.assertEqual(result["test_URL_fragments_reconstructed_pending_review"], 7)
        self.assertEqual(result["full_expressions_recovered_from_fragments"], 8)
        self.assertEqual(result["proposed_entities_with_prior_MAR_corpus"], 6)
        self.assertEqual(result["project_wide_unseen_entities"], 0)
        self.assertFalse(result["science_authorized"])
        self.assertEqual(result["state"], "HOLD_pending_independent_signoff")

    def test_all_six_broader_MAR_snapshots_are_documented(self):
        rows = REVIEW["proposed_entities_scope"]["entities"]
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row["prior_pipeline_source_root_match"] for row in rows))
        self.assertTrue(all(row["snapshot_generated_at"] < "2026-09-08"
                            for row in rows))
        self.assertTrue(all(
            row["approval"] == "hold_pending_methodology_reviewer_decision"
            for row in rows
        ))
        self.assertEqual(
            REVIEW["proposed_entities_scope"]["strictly_project_wide_unseen_entities"], 0
        )

    def test_fixture_promotion_to_live_http_or_automatic_exclusion_fails(self):
        for key, value in [
            ("human_signoff", "approved"), ("auto_exclusion", True),
            ("claimed_redirect_alias", True),
            ("evidence", "historical_verified_live_HTTP_capture"),
        ]:
            with self.subTest(key=key):
                doc = copy.deepcopy(REVIEW)
                doc["fixture_screening"][0][key] = value
                with self.assertRaises(AuditError):
                    self.checked(doc)

    def test_fragment_and_missing_fixture_fail_closed(self):
        doc = copy.deepcopy(REVIEW)
        doc["fixture_screening"].pop()
        with self.assertRaises(AuditError):
            self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        entry = next(
            row for row in doc["fixture_screening"]
            if row["url_expression_status"] ==
            "fragment_of_concatenated_Python_expression"
        )
        entry["url_expression_status"] = "complete_literal_or_root_used_in_test"
        with self.assertRaises(AuditError):
            self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        fragment = next(
            r for r in doc["fixture_screening"]
            if r["url_expression_status"] ==
            "fragment_of_concatenated_Python_expression"
        )
        fragment["reconstructed_complete_expressions"] = []
        with self.assertRaises(AuditError):
            self.checked(doc)

    def test_global_novelty_claim_or_unapproved_entity_is_rejected(self):
        for field, value in [
            ("strictly_project_wide_unseen_entities", 6),
            ("count", 5),
        ]:
            doc = copy.deepcopy(REVIEW)
            doc["proposed_entities_scope"][field] = value
            with self.assertRaises(AuditError):
                self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        doc["proposed_entities_scope"]["entities"][4]["approval"] = "approved"
        with self.assertRaises(AuditError):
            self.checked(doc)

    def test_source_digest_and_prior_root_substitution_fail(self):
        doc = copy.deepcopy(REVIEW)
        doc["basis_inventory_git_blob_sha"] = "a" * 40
        with self.assertRaises(AuditError):
            self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        doc["proposed_entities_scope"]["entities"][0]["proposed_root_url"] = (
            "https://different.example.org/"
        )
        with self.assertRaises(AuditError):
            self.checked(doc)

    def test_no_freeze_or_reviewer_impersonation(self):
        doc = copy.deepcopy(REVIEW)
        doc["scientific_seal_granted"] = True
        with self.assertRaises(AuditError):
            self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        doc["independent_reviewer"]["reviewer_id"] = "imaginary reviewer"
        with self.assertRaises(AuditError):
            self.checked(doc)
        doc = copy.deepcopy(REVIEW)
        doc["gating"]["independent_collection_blocked"] = False
        with self.assertRaises(AuditError):
            self.checked(doc)

    def test_full_verification_refuses_non_git_synthetic_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(AuditError):
                method.verify_at_historical_commit(
                    REVIEW, INVENTORY, INV_BYTES, Path(temp)
                )


if __name__ == "__main__":
    unittest.main()
