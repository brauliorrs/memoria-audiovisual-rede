import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.discovery import (
    DISCOVERY_QUEUE_FILENAME,
    DISCOVERY_REGISTRY_FILENAME,
    DISCOVERY_SUMMARY_FILENAME,
    EUROPE_BASE_INCLUDED_INSTITUTION_DECISION,
    _evaluate_candidate,
    build_discovery_registry,
    build_discovery_summary,
    build_expansion_queue,
    write_discovery_outputs,
)


class DiscoveryTests(unittest.TestCase):
    def test_build_discovery_registry_includes_active_and_candidate_units(self):
        registry_df = build_discovery_registry()
        self.assertFalse(registry_df.empty)
        self.assertIn("ape", registry_df["code"].tolist())
        self.assertIn("ina", registry_df["code"].tolist())
        self.assertIn("euscreen", registry_df["code"].tolist())
        self.assertIn("archivegrid", registry_df["code"].tolist())

    def test_expansion_queue_prioritizes_stage_1_aggregators(self):
        registry_df = build_discovery_registry()
        queue_df = build_expansion_queue(registry_df)
        self.assertFalse(queue_df.empty)
        first_decision = queue_df.iloc[0]["automatic_decision"]
        self.assertEqual(first_decision, "fechamento_europa_agregador_nacional")
        self.assertNotIn("euscreen", queue_df["code"].tolist())

    def test_european_institution_candidate_is_kept_as_gap_or_exception(self):
        candidate = {
            "code": "arquivo-europeu-teste",
            "category_code": "institution",
            "geographic_scope": "Europa",
            "coverage_level": "instituição individual",
            "scope": "arquivo especializado em audiovisual",
            "audiovisual_relevance": "especializado em audiovisual",
            "methodological_fit": "alto",
            "already_covered_by_active_aggregator": False,
        }

        evaluation = _evaluate_candidate(candidate, active_codes={"ape", "ina"})

        self.assertEqual(
            evaluation["automatic_decision"],
            EUROPE_BASE_INCLUDED_INSTITUTION_DECISION,
        )
        self.assertEqual(evaluation["organism_status"], "candidato")

    def test_write_discovery_outputs_materializes_expected_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            outputs = write_discovery_outputs(output_dir)

            self.assertTrue((output_dir / DISCOVERY_REGISTRY_FILENAME).exists())
            self.assertTrue((output_dir / DISCOVERY_QUEUE_FILENAME).exists())
            self.assertTrue((output_dir / DISCOVERY_SUMMARY_FILENAME).exists())
            self.assertFalse(outputs["registry"].empty)
            self.assertFalse(outputs["queue"].empty)
            self.assertFalse(build_discovery_summary(outputs["registry"]).empty)


if __name__ == "__main__":
    unittest.main()
