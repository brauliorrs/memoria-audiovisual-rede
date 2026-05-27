import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.europe_research import (
    EUROPE_RESEARCH_QUEUE_FILENAME,
    EUROPE_RESEARCH_REGISTRY_FILENAME,
    EUROPE_RESEARCH_SUMMARY_FILENAME,
    build_europe_research_queue,
    build_europe_research_registry,
    build_europe_research_summary,
    write_europe_research_outputs,
)


class EuropeResearchTests(unittest.TestCase):
    def test_registry_includes_aggregators_directories_and_active_corpora(self):
        registry_df = build_europe_research_registry()
        unit_codes = registry_df["unit_code"].tolist()

        self.assertIn("ape", unit_codes)
        self.assertIn("ace-members", unit_codes)
        self.assertIn("fiaf-europe-members", unit_codes)
        self.assertIn("fiat-ifta-members", unit_codes)
        self.assertIn("german-digital-library", unit_codes)
        self.assertIn("fiaf-cinemateca-portuguesa", unit_codes)
        self.assertIn("fiat-rtp", unit_codes)
        self.assertIn("fiat-rtve", unit_codes)
        self.assertIn("euscreen-cna", unit_codes)
        self.assertFalse(
            registry_df["unit_type"].astype(str).str.contains("sonoro|musical", case=False).any()
        )

    def test_queue_prioritizes_audiovisual_directories_before_general_sources(self):
        registry_df = build_europe_research_registry()
        queue_df = build_europe_research_queue(registry_df)
        priority_by_code = dict(zip(queue_df["unit_code"], queue_df["queue_priority"]))

        self.assertEqual(priority_by_code["ace-members"], 1)
        self.assertEqual(priority_by_code["fiaf-cinemateca-portuguesa"], 2)
        self.assertEqual(priority_by_code["fiat-rtp"], 2)
        self.assertLess(priority_by_code["fiaf-cinemateca-portuguesa"], priority_by_code["german-digital-library"])
        self.assertEqual(queue_df.iloc[0]["definitive_queue_rank"], 1)
        self.assertIn("video_location_candidate_url", queue_df.columns)
        self.assertFalse(queue_df["queue_decision"].astype(str).str.contains("sonoro", case=False).any())

    def test_summary_and_write_outputs_materialize_queue_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            outputs = write_europe_research_outputs(output_dir)

            self.assertTrue((output_dir / EUROPE_RESEARCH_REGISTRY_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_RESEARCH_QUEUE_FILENAME).exists())
            self.assertTrue((output_dir / EUROPE_RESEARCH_SUMMARY_FILENAME).exists())
            self.assertFalse(outputs["registry"].empty)
            self.assertFalse(outputs["queue"].empty)
            self.assertFalse(build_europe_research_summary(outputs["registry"]).empty)


if __name__ == "__main__":
    unittest.main()
