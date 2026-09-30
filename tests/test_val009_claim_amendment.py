"""Contract tests for the prospective VAL-009 claim amendment.

The amendment narrows the scientific claim before execution. Passing these tests
does not seal or execute the experiment.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AMENDMENT = ROOT / (
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_val009_amendment_v2_3_draft.json"
)
REVIEW = ROOT / (
    "data/digital_infrastructure/ai_experiments/"
    "m3_surface_type_methodology_review_v2_3_draft.json"
)
AUDIT = ROOT / "docs/methodology/m3-corpus-relation-audit.json"


class Val009ClaimAmendmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
        cls.review = json.loads(REVIEW.read_text(encoding="utf-8"))
        cls.audit = json.loads(AUDIT.read_text(encoding="utf-8"))

    def test_amendment_is_draft_and_cannot_authorize_execution(self) -> None:
        self.assertEqual(
            self.amendment["status"],
            "draft_prospective_amendment_pending_independent_protocol_reviewer_signoff",
        )
        self.assertFalse(self.amendment["execution_authorized_by_this_artifact"])
        self.assertFalse(self.amendment["scientific_seal_granted"])
        self.assertFalse(
            self.amendment["base_protocol"]["candidate_reference_is_freeze"]
        )
        self.assertEqual(
            self.amendment["prospective_decision"][
                "independent_protocol_reviewer_status"
            ],
            "pending",
        )
        self.assertIsNone(
            self.amendment["prospective_decision"]["independent_protocol_reviewer_id"]
        )

    def test_six_entities_are_retained_with_only_m3_label_holdout_claim(self) -> None:
        rows = self.amendment["entities"]
        self.assertEqual(len(rows), 6)
        self.assertEqual(
            {row["entity_id"] for row in rows},
            {
                "cinematek", "cinematheque-bretagne", "dr", "ert",
                "estonian_film_archive", "filmoteca_catalunya",
            },
        )
        self.assertTrue(all(row["prior_MAR_corpus"] for row in rows))
        self.assertTrue(
            all(not row["prior_human_labelled_M3_development"] for row in rows)
        )
        review_pairs = {
            (row["entity_id"], row["proposed_root_url"])
            for row in self.review["proposed_entities_scope"]["entities"]
        }
        self.assertEqual(
            {(row["entity_id"], row["root_url"]) for row in rows},
            review_pairs,
        )

    def test_claim_does_not_expand_to_global_project_novelty(self) -> None:
        scope = self.amendment["primary_claim_scope"]
        self.assertIn("previously unlabelled", scope["allowed"])
        self.assertTrue(
            any("wholly unseen" in item for item in scope["not_allowed"])
        )
        self.assertEqual(
            self.amendment["corpus_relationship"][
                "overlap_with_117_human_labelled_M3_development_units"
            ],
            0,
        )
        self.assertFalse(
            self.amendment["corpus_relationship"][
                "direct_runtime_dependency_on_six_general_corpus_exports_found"
            ]
        )
        self.assertEqual(
            self.amendment["corpus_relationship"]["informal_human_familiarity"],
            "cannot_be_proved_or_excluded_retrospectively",
        )

    def test_exclusion_floor_can_only_grow_before_seal(self) -> None:
        exposure = self.amendment["exposure_and_exclusion_state"]
        self.assertEqual(exposure["verified_historical_URL_floor"], 137)
        self.assertEqual(exposure["test_strings_under_methodological_review"], 22)
        self.assertEqual(
            exposure["reconstructed_complete_expressions_from_seven_fragments"], 8
        )
        self.assertEqual(
            exposure["test_strings_automatically_promoted_to_exclusions"], 0
        )
        self.assertEqual(
            exposure["demonstrated_legacy_requested_final_aliases"], 0
        )
        self.assertIn("may grow", exposure["requirement"])
        self.assertIn("may not shrink", exposure["requirement"])

    def test_methodology_review_points_to_amendment_and_stays_hold(self) -> None:
        impact = self.review["selection_and_claim_impact"]
        self.assertEqual(
            impact["prospective_project_methodology_proposal"],
            "retain_six_entities_with_narrow_M3_specific_claim",
        )
        self.assertEqual(
            impact["prospective_amendment_path"],
            "data/digital_infrastructure/ai_experiments/"
            "m3_surface_type_val009_amendment_v2_3_draft.json",
        )
        self.assertTrue(self.review["gating"]["freeze_blocked"])
        self.assertTrue(self.review["gating"]["independent_collection_blocked"])
        self.assertTrue(self.review["gating"]["prediction_release_blocked"])
        self.assertIn(
            "independent_protocol_reviewer_accepts_or_rejects_narrow_claim_before_seal",
            self.review["gating"]["pending"],
        )

    def test_amendment_is_consistent_with_corpus_audit(self) -> None:
        self.assertEqual(
            self.audit["findings"]["overlap_with_117_labelled_M3_development_units"],
            0,
        )
        self.assertTrue(
            self.audit["findings"][
                "held_out_from_labelled_M3_development_sets_for_six"
            ]
        )
        self.assertEqual(
            self.amendment["corpus_relationship"]["audit_path"],
            "docs/methodology/m3-corpus-relation-audit.json",
        )


if __name__ == "__main__":
    unittest.main()
