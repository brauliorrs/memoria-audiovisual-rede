"""Registration, offline metadata counts and no-playback safety regressions."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.corpora import (
    CORPORA, get_corpus_definition, list_active_corpora,
    list_corpora_by_category,
)
from memoria_audiovisual.europe_research import (
    analyzed_corpus_codes, build_europe_research_queue,
    build_europe_research_registry,
)
from memoria_audiovisual.inclusion_queue import select_inclusion_candidates
from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME, PublicationRejected,
    load_published_kavi_rows,
)
from memoria_audiovisual.kavi_finna_registry import load_kavi_metadata_index_summary
from memoria_audiovisual.output_files import (
    KAVI_KUVI_OUTPUT_FILES, FINA_OUTPUT_FILES,
    list_kavi_kuvi_output_filenames,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "output"


class KaviKuviRegistryTests(unittest.TestCase):
    def test_distinct_institution_registry_identity(self):
        definition = get_corpus_definition("kavi_kuvi")
        polish = get_corpus_definition("fina")
        self.assertIs(definition, CORPORA["kavi_kuvi"])
        self.assertEqual(definition["category_code"], "institution")
        self.assertEqual(definition["source_unit_id"], "fiaf-kavi")
        self.assertNotEqual(definition["code"], polish["code"])
        self.assertNotEqual(definition["output_files"], polish["output_files"])
        self.assertIn(definition, list_corpora_by_category("institution"))
        self.assertEqual(definition["metadata_api"], "https://api.finna.fi/v1/search")
        self.assertTrue(definition["metadata_item_links_not_playback"])
        self.assertEqual(definition["media_policy"], "origin_record_link_only_no_player_or_download")

    def test_registration_does_not_skip_number_82_in_analysis_queue(self):
        self.assertFalse(CORPORA["kavi_kuvi"]["counts_as_analyzed_corpus"])
        registry = build_europe_research_registry()
        corpus_codes = analyzed_corpus_codes(registry)
        self.assertNotIn("kavi_kuvi", corpus_codes)
        queue = build_europe_research_queue(registry)
        candidates = select_inclusion_candidates(
            queue.to_dict(orient="records"), limit=1,
        )
        self.assertEqual(candidates[0].unit_code, "fiaf-kavi")
        self.assertEqual(candidates[0].rank, 82)

    def test_index_published_but_no_automatic_media_corpus_activation(self):
        definition = CORPORA["kavi_kuvi"]
        self.assertTrue(definition["published_index_active"])
        self.assertFalse(definition["organism_active"])
        self.assertFalse(definition["monthly_refresh_enabled"])
        self.assertNotIn("kavi_kuvi", {x["code"] for x in list_active_corpora()})
        self.assertNotIn("kavi_kuvi", {x["code"] for x in list_active_corpora(monthly_only=True)})

    def test_standard_output_names_do_not_overwrite_existing_published_csv(self):
        self.assertEqual(KAVI_KUVI_OUTPUT_FILES["analytic_video_catalog"],
                         "kavi_kuvi_catalogo_videos_analitico.csv")
        self.assertNotEqual(KAVI_KUVI_OUTPUT_FILES, FINA_OUTPUT_FILES)
        self.assertEqual(
            list_kavi_kuvi_output_filenames(),
            list(KAVI_KUVI_OUTPUT_FILES.values()),
        )
        self.assertNotIn(CATALOG_FILENAME, KAVI_KUVI_OUTPUT_FILES.values())

    def test_current_published_finna_metadata_keeps_individual_source_links(self):
        summary = load_kavi_metadata_index_summary(OUTPUT_DIR)
        rows, manifest = load_published_kavi_rows(OUTPUT_DIR)
        self.assertTrue(rows)
        self.assertEqual(summary["indexed_metadata_records"], len(rows))
        self.assertEqual(summary["source_record_links"], len(rows))
        self.assertEqual(summary["indexed_metadata_records"], manifest["record_count"])
        self.assertEqual(summary["reference_total_api_video_index"],
                         manifest["expected_total_api_index"])
        self.assertEqual(summary["coverage_status"], "partial")
        self.assertEqual(summary["playable_video_count_verified"], 0)
        self.assertEqual(summary["playback_verification_status"], "unverified")
        self.assertFalse(summary["media_downloaded"])
        self.assertFalse(summary["corpus_activation"])
        self.assertFalse(summary["automatic_refresh_enabled"])
        self.assertTrue(all(row["media_access_status"] == "unverified" for row in rows))
        self.assertTrue(all(row["source_service"] == "finna_api" for row in rows))

    def test_tampered_catalog_is_rejected_before_reporting_counts(self):
        with tempfile.TemporaryDirectory() as temp:
            dest = Path(temp)
            for name in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(OUTPUT_DIR / name, dest / name)
            (dest / CATALOG_FILENAME).write_bytes(
                (dest / CATALOG_FILENAME).read_bytes() + b"forged"
            )
            with self.assertRaises(PublicationRejected):
                load_kavi_metadata_index_summary(dest)

    def test_missing_index_does_not_fake_published_records(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(load_kavi_metadata_index_summary(temp), {})


if __name__ == "__main__":
    unittest.main()
