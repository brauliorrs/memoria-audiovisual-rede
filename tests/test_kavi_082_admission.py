"""Regression tests for fail-closed KAVI/Kuvi G4, no network or media."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_kavi_082_admission import evaluate

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs" / "engineering" / "kavi-082-admission-evidence.json"
URL = "https://github.com/brauliorrs/memoria-audiovisual-rede/issues/59"
SHA = "a" * 64


def baseline() -> dict:
    return json.loads(EVIDENCE.read_text(encoding="utf-8"))


def synthetic_complete() -> dict:
    """Synthetic scenario only; never assert empirical validation from it."""
    dossier = copy.deepcopy(baseline())
    count = 200
    snap = dossier["snapshot"]
    snap["expected_total"] = count
    snap["completeness"] = "complete"
    snap["terminal_cursor_exhausted"] = True
    snap["snapshot_freshness_verified"] = True
    q = dossier["source_quality"]
    q["human_film_classification_reviewed"] = 24
    q["provenance_labeled_records"] = count
    q["custody_labeled_records"] = count
    q["media_access_labeled_records"] = count
    q["sampling_plan_url"] = URL
    q["curatorial_review_evidence_url"] = URL
    q["per_record_audit_evidence_url"] = URL
    q["per_record_audit_sha256"] = SHA
    g = dossier["governance"]
    g["independent_reviewers"] = ["reviewer-1", "reviewer-2"]
    g["review_status"] = "completed"
    g["review_document_url"] = URL
    dossier["declared_state"] = "ready_for_human_review"
    return dossier


class AdmissionEvidenceTests(unittest.TestCase):
    def test_actual_october_19_evidence_is_hold(self):
        observed = baseline()
        r = evaluate(observed)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertEqual(r["observed_records"], 200)
        self.assertEqual(r["reference_total"], 138393)
        self.assertFalse(r["promotion_authorized"])
        for reason in (
            "partial_enumeration",
            "incomplete_record_coverage",
            "snapshot_freshness_unverified",
            "human_film_semantics_unreviewed",
            "incomplete_provenance_labeled_records",
            "incomplete_custody_labeled_records",
            "incomplete_media_access_labeled_records",
            "independent_review_incomplete",
        ):
            self.assertIn(reason, r["reasons"])

    def test_synthetic_full_dossier_only_readiness_not_admission(self):
        r = evaluate(synthetic_complete())
        self.assertEqual(r["status"], "READY_FOR_HUMAN_ADJUDICATION")
        self.assertEqual(r["reasons"], [])
        self.assertIs(r["promotion_authorized"], False)

    def test_claim_ready_on_partial_data_is_denied(self):
        d = baseline()
        d["declared_state"] = "ready_for_human_review"
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("unsupported_ready_declaration", r["reasons"])

    def test_even_complete_without_human_review_is_hold(self):
        d = synthetic_complete()
        d["governance"]["independent_reviewers"] = []
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("independent_review_incomplete", r["reasons"])

    def test_complete_without_per_record_labels_is_hold(self):
        d = synthetic_complete()
        d["source_quality"]["media_access_labeled_records"] -= 1
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("incomplete_media_access_labeled_records", r["reasons"])

    def test_no_full_coverage_without_terminal_cursor(self):
        d = synthetic_complete()
        d["snapshot"]["terminal_cursor_exhausted"] = False
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("terminal_cursor_unverified", r["reasons"])

    def test_complete_flag_cannot_override_count_gap(self):
        d = baseline()
        d["snapshot"]["completeness"] = "complete"
        d["snapshot"]["terminal_cursor_exhausted"] = True
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("incomplete_record_coverage", r["reasons"])

    def test_duplicate_ids_even_in_complete_state_is_hold(self):
        d = synthetic_complete()
        d["snapshot"]["duplicate_ids"] = 1
        r = evaluate(d)
        self.assertEqual(r["status"], "HOLD_PROVISIONAL")
        self.assertIn("duplicate_or_missing_records", r["reasons"])

    def test_prohibit_corpus_activation_even_synthetic(self):
        d = synthetic_complete()
        d["governance"]["corpus_activation"] = True
        r = evaluate(d)
        self.assertEqual(r["status"], "REJECT_INVALID_EVIDENCE")
        self.assertFalse(r["promotion_authorized"])

    def test_reject_claim_of_different_scope(self):
        for key, value in (
            ("format_code", "0/Book/"),
            ("provider_code", "0/Another/"),
            ("api_endpoint", "https://elonet.finna.fi/Record/anything"),
            ("media_policy", "embed_player"),
            ("metadata_license", "license_undetermined"),
        ):
            with self.subTest(key=key):
                d = baseline()
                d["scope"][key] = value
                self.assertEqual(evaluate(d)["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_bogus_hash_and_unsafe_evidence_url(self):
        d = baseline()
        d["snapshot"]["record_id_sequence_sha256"] = "not-a-hash"
        d["snapshot"]["evidence_url"] = "http://localhost/false"
        r = evaluate(d)
        self.assertEqual(r["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_duplicated_independent_reviewers(self):
        d = synthetic_complete()
        d["governance"]["independent_reviewers"] = ["one", "one"]
        self.assertEqual(evaluate(d)["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_false_class_totals(self):
        d = baseline()
        d["source_quality"]["film_id_candidates"] = 201
        self.assertEqual(evaluate(d)["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_claims_exceeding_observed(self):
        d = baseline()
        d["source_quality"]["custody_labeled_records"] = 201
        self.assertEqual(evaluate(d)["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_boolean_pretending_integer(self):
        d = baseline()
        d["snapshot"]["expected_total"] = True
        self.assertEqual(evaluate(d)["status"], "REJECT_INVALID_EVIDENCE")

    def test_reject_non_object(self):
        self.assertEqual(evaluate([])["status"], "REJECT_INVALID_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
