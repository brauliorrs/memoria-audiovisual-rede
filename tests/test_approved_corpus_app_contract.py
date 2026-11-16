"""Static public-search contract: admitted fiches remain origin-only metadata."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AdmissionWiringTests(unittest.TestCase):
    def test_global_catalog_only_reads_approved_manifest_admissions(self):
        source = (ROOT / "app/streamlit_app.py").read_text(encoding="utf-8-sig")
        self.assertIn("load_all_approved_corpora(OUTPUT_DIR)", source)
        self.assertIn("existing_origin_links", source)
        self.assertIn('identity = (definition["short_label"], record["video_link"])', source)
        self.assertIn('if identity in existing_origin_links:', source)
        self.assertIn('supplemental["source_page_url"] = supplemental["source_record_url"]', source)

    def test_metadata_only_rows_are_excluded_from_public_video_filter(self):
        source = (ROOT / "app/streamlit_app.py").read_text(encoding="utf-8-sig")
        self.assertIn('{"finna_api", "mar_admitted_metadata"}', source)
        self.assertIn("~kavi_metadata | explicitly_playable", source)
        self.assertIn('metric("Registros catalogados", len(catalog_df))', source)

    def test_no_active_crawler_or_database_write_in_admission(self):
        source = (ROOT / "src/memoria_audiovisual/approved_corpus_admission.py").read_text()
        self.assertNotIn("requests.", source)
        self.assertNotIn("httpx.", source)
        self.assertNotIn("psycopg", source)
        self.assertNotIn("subprocess", source)
        self.assertNotIn(".write_text(", source)
        self.assertNotIn(".write_bytes(", source)
        self.assertNotIn(".unlink(", source)


if __name__ == "__main__":
    unittest.main()
