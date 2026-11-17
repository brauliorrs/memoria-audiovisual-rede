"""KAVI direct route must expose only signed partial metadata records."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from memoria_audiovisual.kavi_direct_access import (
    RELEASE_MARKER, read_kavi_direct_index, records_for_display,
)
from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "output"


class KaviDirectAccessTests(unittest.TestCase):
    def test_real_200_fiches_are_available_without_global_search_filters(self):
        result = read_kavi_direct_index(OUT)
        self.assertEqual(result.status, "published_partial_metadata")
        self.assertEqual(result.manifest["record_count"], 200)
        self.assertEqual(result.manifest["coverage_status"], "partial")
        self.assertFalse(result.manifest["corpus_activation"])
        self.assertFalse(result.manifest["media_downloaded"])
        self.assertEqual(len(result.rows), 200)
        display = records_for_display(result)
        self.assertEqual(len(display), 200)
        self.assertEqual(len({r["Identificador"] for r in display}), 200)
        self.assertEqual(len({r["Acessar ficha na origem"] for r in display}), 200)
        self.assertTrue(all(r["Acessar ficha na origem"].startswith("https://")
                            for r in display))
        self.assertTrue(all("Acessar ficha na origem" in r for r in display))
        self.assertTrue(all("Título" in r for r in display))
        self.assertTrue(all("Ano" in r for r in display))
        self.assertTrue(all("media" not in key.lower() for r in display for key in r))

    def test_missing_deploy_files_report_missing_instead_of_fake_records(self):
        with tempfile.TemporaryDirectory() as root:
            result = read_kavi_direct_index(root)
            self.assertEqual(result.status, "missing_release_assets")
            self.assertEqual(records_for_display(result), [])

    def test_missing_one_of_the_files_reports_integrity_hold(self):
        with tempfile.TemporaryDirectory() as root:
            shutil.copyfile(OUT / CATALOG_FILENAME, Path(root) / CATALOG_FILENAME)
            result = read_kavi_direct_index(root)
            self.assertEqual(result.status, "hold_integrity")
            self.assertEqual(result.rows, [])

    def test_tampering_reports_hold_and_no_published_fiches(self):
        with tempfile.TemporaryDirectory() as root:
            for filename in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(OUT / filename, Path(root) / filename)
            p = Path(root) / CATALOG_FILENAME
            p.write_bytes(p.read_bytes() + b"FAKE")
            result = read_kavi_direct_index(root)
            self.assertEqual(result.status, "hold_integrity")
            self.assertEqual(records_for_display(result), [])

    def test_public_app_has_direct_link_and_deployment_version_marker(self):
        source = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8-sig")
        self.assertIn('st.query_params.get("acervo") == "kavi"', source)
        self.assertIn('st.query_params["acervo"] = "kavi"', source)
        self.assertIn("render_kavi_direct_view()", source)
        self.assertIn('key="open-kavi-direct-index"', source)
        self.assertIn("Versão da interface:", source)
        self.assertIn("read_kavi_direct_index(OUTPUT_DIR)", source)
        self.assertIn("records_for_display(result)", source)
        self.assertIn('st.session_state["mar-catalog-release"] = RELEASE_MARKER', source)
        self.assertEqual(RELEASE_MARKER, "MAR-KAVI-DIRECT-20261117")
        self.assertNotIn("requests.get(", source[source.index("def render_kavi_direct_view"):source.index("# Após uma nova release")])
        self.assertNotIn("psycopg", (ROOT / "src/memoria_audiovisual/kavi_direct_access.py").read_text())


if __name__ == "__main__":
    unittest.main()
