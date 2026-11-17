"""Central MAR catalogue: KAVI is discoverable, not a playable video corpus."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from memoria_audiovisual.corpora import CORPORA, CORPUS_CATEGORIES
from memoria_audiovisual.kavi_finna_public_catalog import (
    CATALOG_FILENAME, MANIFEST_FILENAME, PublicationRejected,
    load_published_kavi_rows,
)
from memoria_audiovisual.research_catalog_projection import (
    APPROVED_METADATA_STATUS, KAVI_PARTIAL_STATUS, LEGACY_STATUS,
    only_verified_public_playback, project_kavi_search_records,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "output"


def project(rows, manifest):
    unit = CORPORA["kavi_kuvi"]
    category = CORPUS_CATEGORIES[unit["category_code"]]
    return project_kavi_search_records(
        rows, manifest, corpus_label=unit["short_label"],
        institution_label=unit["label"], category_label=category["label"],
    )


class CentralCatalogKaviTests(unittest.TestCase):
    def test_exactly_200_already_approved_kavi_fiches_are_searchable(self):
        rows, manifest = load_published_kavi_rows(OUT)
        self.assertEqual(len(rows), 200)
        self.assertEqual(manifest["record_count"], 200)
        self.assertEqual(manifest["coverage_status"], "partial")
        projected = project(rows, manifest)
        self.assertEqual(len(projected), 200)
        self.assertEqual(len({x["source_record_id"] for x in projected}), 200)
        self.assertEqual(len({x["source_record_url"] for x in projected}), 200)
        self.assertTrue(all("KAVI / Kuvi" in x["corpus"] for x in projected))
        self.assertTrue(all(x["documentary_status"] == KAVI_PARTIAL_STATUS for x in projected))
        self.assertTrue(all(x["country"] == "Finland" for x in projected))
        self.assertTrue(all(x["platform"] == "Finna / Elonet" for x in projected))
        self.assertTrue(all(x["source_service"] == "finna_api" for x in projected))
        self.assertTrue(all(x["source_record_url"] == x["video_link"] for x in projected))
        self.assertTrue(all(not x["scientific_corpus_validated"] for x in projected))
        self.assertTrue(all(x["media_access_status"] == "unverified" for x in projected))
        self.assertTrue(all(x["media_rights_status"] == "not_verified" for x in projected))
        self.assertTrue(all(x["record_review_status"] == "unreviewed" for x in projected))

        catalog = pd.DataFrame(projected)
        found = catalog.loc[
            catalog["corpus"].str.contains("KAVI", case=False, regex=False)
        ]
        self.assertEqual(len(found), 200)
        self.assertEqual(len(only_verified_public_playback(catalog)), 0)
        self.assertNotIn("verified_public_playback", set(catalog["media_access_status"]))

    def test_duplicate_ids_or_origin_links_in_candidate_projection_reject_whole_batch(self):
        rows, manifest = load_published_kavi_rows(OUT)
        duplicated_id = dict(rows[1])
        duplicated_id["source_record_id"] = rows[0]["source_record_id"]
        duplicated_url = dict(rows[1])
        duplicated_url["video_link"] = rows[0]["video_link"]
        duplicated_url["source_record_url"] = rows[0]["video_link"]
        for duplicate in (duplicated_id, duplicated_url):
            candidate = [rows[0], duplicate]
            local_manifest = dict(manifest, record_count=2)
            self.assertEqual(project(candidate, local_manifest), [])

    def test_partial_or_unreviewed_index_does_not_become_scientifically_approved(self):
        self.assertNotEqual(KAVI_PARTIAL_STATUS, APPROVED_METADATA_STATUS)
        self.assertNotEqual(KAVI_PARTIAL_STATUS, LEGACY_STATUS)
        rows, manifest = load_published_kavi_rows(OUT)
        for patch in (
            {"metadata_publication_approved": False},
            {"status": "draft"},
            {"coverage_status": "complete"},
            {"corpus_activation": True},
            {"record_count": 199},
        ):
            with self.subTest(patch=patch):
                self.assertEqual(project(rows, dict(manifest, **patch)), [])

    def test_invalid_sha_fails_public_loader_and_never_projects(self):
        with tempfile.TemporaryDirectory() as folder:
            for file in (CATALOG_FILENAME, MANIFEST_FILENAME):
                shutil.copyfile(OUT / file, Path(folder) / file)
            path = Path(folder) / CATALOG_FILENAME
            path.write_bytes(path.read_bytes() + b"not-authorized")
            with self.assertRaises(PublicationRejected):
                rows, manifest = load_published_kavi_rows(folder)
                project(rows, manifest)

    def test_verified_public_playback_requires_explicit_status_and_link(self):
        frame = pd.DataFrame([
            {"video_link": "https://www.finna.fi/Record/1",
             "media_access_status": "unverified"},
            {"video_link": "https://origin.example.org/item/2",
             "media_access_status": "verified_public_playback"},
            {"video_link": "", "media_access_status": "verified_public_playback"},
            {"video_link": "https://origin.example.org/item/3",
             "media_access_status": "not_verified"},
        ])
        found = only_verified_public_playback(frame)
        self.assertEqual(found["video_link"].tolist(), [
            "https://origin.example.org/item/2",
        ])
        self.assertEqual(len(only_verified_public_playback(frame.drop(columns=[
            "media_access_status",
        ]))), 0)


class CentralCatalogNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (ROOT / "app" / "streamlit_app.py").read_text(encoding="utf-8-sig")

    def test_landing_catalogue_is_default_and_legacy_panels_are_secondary(self):
        self.assertIn('st.session_state.setdefault("global-research-open", True)', self.source)
        self.assertIn("Explorar painéis e instituições", self.source)
        self.assertIn("Voltar ao catálogo central", self.source)
        self.assertIn('"Instituições e unidades"', self.source)
        self.assertIn('key="central-unit-selector"', self.source)
        self.assertNotIn("top_level_tabs = st.tabs(", self.source)

    def test_kavi_only_from_verified_public_manifest(self):
        self.assertIn("load_published_kavi_rows(OUTPUT_DIR)", self.source)
        self.assertIn("project_kavi_search_records(", self.source)
        self.assertIn('if corpus_def["code"] == "kavi_kuvi":', self.source)
        self.assertIn("load_admissions_with_individual_holds(OUTPUT_DIR)", self.source)
        self.assertIn("APPROVED_METADATA_STATUS", self.source)
        self.assertIn("LEGACY_STATUS", self.source)

    def test_explicit_institution_and_validation_filters_do_not_preselect_playback(self):
        self.assertIn("selected_institution=selected_institution", self.source)
        self.assertIn("selected_documentary_status=selected_documentary_status", self.source)
        self.assertIn("only_verified_public_playback(filtered_df)", self.source)
        self.assertIn('"Somente vídeos com reprodução pública verificada"', self.source)
        self.assertIn("value=False,", self.source)
        self.assertIn('documentary_status": "situação documental"', self.source)

    def test_no_new_media_or_database_dependencies(self):
        from memoria_audiovisual import research_catalog_projection as module
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in ("requests.", "httpx.", "psycopg", ".write_bytes(", ".write_text(", "streamlit"):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
