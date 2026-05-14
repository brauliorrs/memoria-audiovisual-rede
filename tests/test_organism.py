import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.organism import (
    ORGANISM_ACTIVE_CORPORA_FILENAME,
    ORGANISM_CYCLE_RESULTS_FILENAME,
    ORGANISM_CYCLE_TIMELINE_FILENAME,
    ORGANISM_MONTHLY_CYCLE_FILENAME,
    build_active_corpora_registry,
    build_corpus_refresh_status,
    build_cycle_results_entries,
    build_cycle_timeline_entry,
    build_monthly_cycle_manifest,
    write_active_corpora_registry,
    write_cycle_history,
    write_monthly_cycle_manifest,
)


class OrganismTests(unittest.TestCase):
    def test_build_active_corpora_registry_includes_expected_columns(self):
        registry_df = build_active_corpora_registry()
        self.assertFalse(registry_df.empty)
        for column in [
            "code",
            "corpus",
            "category_code",
            "category_label",
            "monthly_refresh_enabled",
            "run_script",
            "check_script",
        ]:
            self.assertIn(column, registry_df.columns)

    def test_write_monthly_cycle_manifest_and_registry_create_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            manifest = write_monthly_cycle_manifest(
                started_at="2026-05-01T00:00:00Z",
                finished_at="2026-05-01T00:10:00Z",
                cycle_results=[
                    {
                        "code": "ape",
                        "status": "success",
                        "observation_key": "ape:2026-05-01T00:00:00Z",
                    }
                ],
                output_dir=output_dir,
            )
            registry_df = write_active_corpora_registry(output_dir)

            self.assertEqual(manifest["cycle_type"], "mensal")
            self.assertTrue((output_dir / ORGANISM_MONTHLY_CYCLE_FILENAME).exists())
            self.assertTrue((output_dir / ORGANISM_ACTIVE_CORPORA_FILENAME).exists())
            self.assertFalse(registry_df.empty)

    def test_build_monthly_cycle_manifest_counts_successes(self):
        manifest = build_monthly_cycle_manifest(
            started_at="2026-05-01T00:00:00Z",
            finished_at="2026-05-01T00:10:00Z",
            cycle_results=[
                {"code": "ape", "status": "success"},
                {"code": "ina", "status": "failed"},
            ],
            selected_corpora=["ape", "ina"],
        )
        self.assertEqual(manifest["successful_corpora_total"], 1)
        self.assertEqual(manifest["failed_corpora_total"], 1)
        self.assertEqual(manifest["selected_corpora_total"], 2)

    def test_write_cycle_history_creates_timeline_and_results(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            manifest = build_monthly_cycle_manifest(
                started_at="2026-05-01T00:00:00Z",
                finished_at="2026-05-01T00:10:00Z",
                cycle_results=[
                    {
                        "code": "ina",
                        "label": "INA",
                        "short_label": "INA",
                        "category_code": "institution",
                        "coverage_level": "instituição individual",
                        "status": "success",
                    }
                ],
                selected_corpora=["ina"],
            )
            history = write_cycle_history(manifest, output_dir)

            self.assertTrue((output_dir / ORGANISM_CYCLE_TIMELINE_FILENAME).exists())
            self.assertTrue((output_dir / ORGANISM_CYCLE_RESULTS_FILENAME).exists())
            self.assertEqual(len(history["cycle_timeline"]), 1)
            self.assertEqual(len(history["cycle_results"]), 1)
            self.assertEqual(history["cycle_results"].iloc[0]["code"], "ina")

    def test_build_corpus_refresh_status_marks_partial_cycle_pending(self):
        registry_df = build_active_corpora_registry()
        manifest = build_monthly_cycle_manifest(
            started_at="2026-05-01T00:00:00Z",
            finished_at="2026-05-01T00:10:00Z",
            cycle_results=[
                {
                    "code": "ina",
                    "label": "INA",
                    "short_label": "INA",
                    "category_code": "institution",
                    "coverage_level": "instituição individual",
                    "status": "success",
                    "snapshot_generated_at": "2026-05-01T00:09:00Z",
                    "observation_key": "ina:2026-05-01T00:09:00Z",
                }
            ],
            selected_corpora=["ina"],
        )
        cycle_results_df = build_cycle_results_entries(manifest)
        refresh_df = build_corpus_refresh_status(
            registry_df,
            cycle_manifest=manifest,
            cycle_results_df=cycle_results_df,
            snapshot_metadata_by_code={
                "ape": {"generated_at": "2026-04-15T00:00:00Z", "observation_key": "ape:2026-04-15T00:00:00Z"},
                "ina": {"generated_at": "2026-05-01T00:09:00Z", "observation_key": "ina:2026-05-01T00:09:00Z"},
            },
            reference_timestamp="2026-05-05T00:00:00Z",
        )

        ape_state = refresh_df.loc[refresh_df["code"] == "ape", "refresh_state"].iloc[0]
        ina_state = refresh_df.loc[refresh_df["code"] == "ina", "refresh_state"].iloc[0]
        self.assertEqual(ape_state, "Pendente no ciclo parcial mais recente")
        self.assertEqual(ina_state, "Atualizado no último ciclo")

    def test_build_corpus_refresh_status_marks_stale_corpus(self):
        registry_df = build_active_corpora_registry()
        refresh_df = build_corpus_refresh_status(
            registry_df,
            cycle_manifest=None,
            cycle_results_df=None,
            snapshot_metadata_by_code={
                "ape": {"generated_at": "2026-01-01T00:00:00Z", "observation_key": "ape:2026-01-01T00:00:00Z"},
                "ina": {"generated_at": "2026-05-01T00:00:00Z", "observation_key": "ina:2026-05-01T00:00:00Z"},
            },
            reference_timestamp="2026-05-20T00:00:00Z",
        )

        ape_state = refresh_df.loc[refresh_df["code"] == "ape", "refresh_state"].iloc[0]
        ina_state = refresh_df.loc[refresh_df["code"] == "ina", "refresh_state"].iloc[0]
        self.assertEqual(ape_state, "Atualização atrasada")
        self.assertEqual(ina_state, "Em dia")


if __name__ == "__main__":
    unittest.main()
