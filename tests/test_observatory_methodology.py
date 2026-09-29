"""Documentary consistency checks for the MAR scientific methods proposal.

These assertions protect epistemic distinctions; they do not validate any
scientific detector, sample, model or inference.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METHODS = ROOT / "docs/methodology/mar-scientific-methodology.md"
MATRIX = ROOT / "docs/methodology/instrument-status.json"


class ObservatoryMethodologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.methodology = METHODS.read_text(encoding="utf-8")
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_canonical_question_and_documented_scope(self) -> None:
        question = (
            "Sob quais condições infraestruturais, institucionais, técnicas e "
            "culturais os acervos audiovisuais se tornam visíveis, invisíveis, "
            "restritos ou instáveis em ambientes digitais?"
        )
        self.assertEqual(self.matrix["central_question"], question)
        self.assertIn(question, self.methodology)
        self.assertIn("observatório científico", self.methodology)
        self.assertIn("versão básica", self.methodology)

    def test_no_automatic_scientific_approval(self) -> None:
        invariants = self.matrix["invariants"]
        self.assertTrue(invariants)
        self.assertTrue(all(value is False for value in invariants.values()))
        self.assertIn("proposal_for_academic_review", self.matrix["document_status"])
        self.assertEqual(
            self.matrix["research_protocol_notes"]["VAL009"]["status"],
            "draft_hold_pending_methodology_and_roles",
        )

    def test_instrument_research_roles_are_separated(self) -> None:
        components = self.matrix["components"]
        names = [component["id"] for component in components]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(
            set(names),
            {
                "corpus", "public_search_and_discovery",
                "technical_infrastructure_audit", "institutional_ai_evidence",
                "M3_surface_typing", "M4_item_surface_gate",
                "evidence_and_governance", "longitudinal_observatory",
                "composite_visibility_index",
            },
        )
        for component in components:
            for field in (
                "scientific_role", "implementation", "technical_evidence",
                "empirical_validation", "may_infer", "must_not_infer",
            ):
                self.assertTrue(component[field], (component["id"], field))
            for relative in component["technical_evidence"]:
                self.assertTrue((ROOT / relative).is_file(), relative)

    def test_ai_evidence_is_not_media_generation_detection(self) -> None:
        ai = next(x for x in self.matrix["components"]
                  if x["id"] == "institutional_ai_evidence")
        self.assertIn("video", ai["must_not_infer"])
        self.assertIn("não faz parte do escopo validado", self.methodology)
        self.assertIn("Ausência", self.methodology)
        self.assertFalse(
            self.matrix["invariants"]["absence_of_public_ai_signal_implies_no_institutional_ai"]
        )

    def test_validation_is_distinct_from_implementation(self) -> None:
        val = self.matrix["research_protocol_notes"]["VAL009"]
        self.assertEqual(val["known_historical_urls_floor"], 137)
        self.assertEqual(val["test_strings_pending_independent_review"], 22)
        self.assertTrue(val["six_proposed_institutions_in_broader_prior_MAR_corpus"])
        self.assertEqual(val["indirect_development_exposure"], "not_yet_resolved")
        self.assertIn("VAL-007", self.methodology)
        self.assertIn("não selada e não executada", self.methodology)

    def test_readme_has_methodology_navigation(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "docs/methodology/mar-scientific-methodology.md", readme
        )
        self.assertIn("docs/methodology/instrument-status.json", readme)


if __name__ == "__main__":
    unittest.main()
