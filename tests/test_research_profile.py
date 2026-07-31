import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "memoria_audiovisual" / "research_profile.py"
SPEC = spec_from_file_location("research_profile", MODULE_PATH)
research_profile = module_from_spec(SPEC)
SPEC.loader.exec_module(research_profile)


class ResearchProfileTests(unittest.TestCase):
    def test_parameter_rows_have_dashboard_contract(self):
        rows = research_profile.build_research_parameter_rows()

        self.assertGreaterEqual(len(rows), 8)
        for row in rows:
            self.assertIn("parâmetro científico", row)
            self.assertIn("tradução na plataforma", row)
            self.assertIn("evidência atual", row)
            self.assertIn("estado", row)

    def test_status_summary_counts_all_rows(self):
        rows = research_profile.build_research_parameter_rows()
        summary = research_profile.summarize_research_parameter_status(rows)

        self.assertEqual(sum(summary.values()), len(rows))
        self.assertGreater(summary.get("implementado", 0), 0)
        self.assertGreater(summary.get("em adaptação", 0), 0)

    def test_positioning_keeps_platform_multiuse(self):
        self.assertEqual(
            research_profile.RESEARCH_PLATFORM_POSITIONING["função"],
            "plataforma científica aberta",
        )
        self.assertIn("pós-doutorado", research_profile.RESEARCH_PLATFORM_POSITIONING["usos"])
        self.assertIn("visíveis", research_profile.RESEARCH_MAIN_QUESTION)
        self.assertGreaterEqual(len(research_profile.build_research_next_adjustment_rows()), 4)


if __name__ == "__main__":
    unittest.main()
