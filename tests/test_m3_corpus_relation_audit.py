"""Consistency tests for the documentary audit linking prior MAR corpora and M3.

These tests guard the stated lineage; they are not an independent validation of M3.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/methodology/m3-corpus-relation-audit.json"
REPORT = ROOT / "docs/methodology/m3-corpus-relation-audit.md"


class M3CorpusRelationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        cls.report = REPORT.read_text(encoding="utf-8")

    def test_six_prior_corpora_are_project_known_but_label_held_out(self) -> None:
        findings = self.audit["findings"]
        self.assertTrue(findings["six_entities_preexisted_M3"])
        self.assertEqual(findings["overlap_with_117_labelled_M3_development_units"], 0)
        self.assertTrue(findings["held_out_from_labelled_M3_development_sets_for_six"])
        self.assertFalse(findings["project_wide_entity_novelty_for_six"])

    def test_labelled_development_lineage_is_exactly_117(self) -> None:
        lineage = self.audit["labelled_M3_development_lineage"]
        self.assertEqual([row["units"] for row in lineage], [17, 33, 36, 31])
        self.assertEqual(sum(row["units"] for row in lineage), 117)
        labels = {entity for row in lineage for entity in row["entities"]}
        prior = {row["entity_id"] for row in self.audit["six_prior_corpora"]}
        self.assertTrue(labels.isdisjoint(prior))

    def test_no_claim_of_unrecorded_human_independence(self) -> None:
        self.assertEqual(
            self.audit["findings"]["indirect_manual_exposure_to_general_corpus"],
            "not_determinable_from_repository",
        )
        text = " ".join(self.audit["epistemic_classification"]["not_proven"])
        self.assertIn("never viewed", text)
        self.assertIn("zero cognitive influence", text)

    def test_candidate_23_trace_points_to_val007_not_six_corpora(self) -> None:
        trace = self.audit["explicit_2_3_design_trace"]
        self.assertEqual(trace["source"], "VAL-007 post-validation error analysis")
        self.assertEqual(
            {x["source_entity"] for x in trace["examples"]},
            {"cinemateca-portuguesa", "cinematheque-francaise",
             "home-movies-memoryscapes"},
        )
        self.assertNotEqual(
            {x["source_entity"] for x in trace["examples"]},
            {x["entity_id"] for x in self.audit["six_prior_corpora"]},
        )

    def test_recommended_claim_is_narrow_and_science_stays_unsigned(self) -> None:
        decision = self.audit["methodological_decision_recommended"]
        self.assertIn("previously unlabelled M3 surfaces", decision["VAL009_claim_allowed_if_formally_approved"])
        self.assertIn("wholly unseen", decision["VAL009_claim_not_allowed"])
        self.assertEqual(
            decision["status"],
            "recommendation_pending_formal_protocol_reviewer_signoff",
        )
        self.assertIn("não há evidência de vazamento direto", self.report.lower())
        self.assertIn("não é uma assinatura independente", self.report.lower())


if __name__ == "__main__":
    unittest.main()
