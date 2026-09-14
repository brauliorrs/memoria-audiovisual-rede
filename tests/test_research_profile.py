import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "memoria_audiovisual" / "research_profile.py"
SPEC = spec_from_file_location("research_profile", MODULE_PATH)
research_profile = module_from_spec(SPEC)
SPEC.loader.exec_module(research_profile)


def identity_translator(key):
    return key


class ResearchProfileTests(unittest.TestCase):
    def test_parameter_rows_have_semantic_catalogue_contract(self):
        rows = research_profile.build_research_parameter_rows(identity_translator)

        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            self.assertIn("research.columns.parameter", row)
            self.assertIn("research.columns.platform_translation", row)
            self.assertIn("research.columns.current_evidence", row)
            self.assertIn("research.columns.status", row)
            self.assertTrue(row["research.columns.parameter"].startswith("research.parameter."))
            self.assertTrue(row["research.columns.status"].startswith("research.status."))

    def test_status_summary_counts_all_rows(self):
        summary = research_profile.summarize_research_parameter_status()

        self.assertEqual(sum(summary.values()), len(research_profile.RESEARCH_PARAMETER_ROWS))
        self.assertGreater(summary.get("implemented", 0), 0)
        self.assertGreater(summary.get("adapting", 0), 0)
        self.assertGreater(summary.get("to_develop", 0), 0)

    def test_positioning_keeps_platform_multiuse_as_semantic_keys(self):
        positioning = dict(research_profile.RESEARCH_PLATFORM_POSITIONING)

        self.assertEqual(
            positioning["research.positioning.function.label"],
            "research.positioning.function.value",
        )
        self.assertEqual(
            positioning["research.positioning.uses.label"],
            "research.positioning.uses.value",
        )
        self.assertEqual(research_profile.RESEARCH_MAIN_QUESTION, "research.profile.main_question")

        positioning_rows = research_profile.build_research_positioning_rows(identity_translator)
        self.assertEqual(len(positioning_rows), len(research_profile.RESEARCH_PLATFORM_POSITIONING))
        self.assertGreaterEqual(
            len(research_profile.build_research_next_adjustment_rows(identity_translator)),
            4,
        )

    def test_public_research_profile_contains_only_catalogue_keys(self):
        self.assertTrue(research_profile.RESEARCH_WORKING_TITLE.startswith("research."))
        self.assertTrue(research_profile.RESEARCH_SUBTITLE.startswith("research."))
        self.assertTrue(research_profile.RESEARCH_MAIN_QUESTION.startswith("research."))

        for parameter, platform, evidence, status in research_profile.RESEARCH_PARAMETER_ROWS:
            self.assertTrue(parameter.startswith("research.parameter."))
            self.assertTrue(platform.startswith("research.parameter."))
            self.assertTrue(evidence.startswith("research.parameter."))
            self.assertIn(status, research_profile.STATUS_KEYS)


if __name__ == "__main__":
    unittest.main()
