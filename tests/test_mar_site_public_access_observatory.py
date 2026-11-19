"""Contract tests: historical access visibility must not authorize new publication."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
HISTORICAL = json.loads((SITE / "data/public-access-observatory.json").read_text(encoding="utf-8"))
KAVI = json.loads((SITE / "data/kavi-public.json").read_text(encoding="utf-8"))


class PublicAccessObservatoryTests(unittest.TestCase):
    def test_historical_index_totals_and_unique_corpora(self):
        self.assertEqual(HISTORICAL["summary"]["historicalMaterializedTotal"], 194057)
        self.assertEqual(HISTORICAL["summary"]["historicalPublicSurfaceRecords"], 165134)
        self.assertEqual(HISTORICAL["summary"]["historicalRestrictedRecords"], 28923)
        self.assertEqual(HISTORICAL["summary"]["historicalCorpusRows"], 60)
        self.assertEqual(len(HISTORICAL["corpora"]), 63)
        self.assertEqual(len({r["code"] for r in HISTORICAL["corpora"]}), 63)

    def test_all_non_kavi_records_remain_nonpublic(self):
        self.assertTrue(HISTORICAL["notLive"])
        self.assertTrue(HISTORICAL["publicAccessIsNotLicense"])
        self.assertTrue(HISTORICAL["publicationOfIndividualRecordsNotAuthorizedByThisFile"])
        self.assertEqual(HISTORICAL["kaviSiteApprovedRecords"], 200)
        self.assertEqual(KAVI["total"], 200)
        for entry in HISTORICAL["corpora"]:
            self.assertEqual(entry["recordDisplay"], "not_authorized_for_new_site")
            self.assertIn(entry["humanAccessEvidence"], {
                "not_revalidated_in_this_migration",
                "official_sample_observed",
                "hold_new_access_unverified",
                "portal_search_interface_observed",
                "institutional_route_observed",
                "aggregator_profile_observed",
                "environment_limited",
            })
            self.assertTrue(entry["humanAccessNote"])
            self.assertTrue(entry["reviewReason"])

    def test_eye_czech_human_access_separate_from_legal_status(self):
        by_code = {row["code"]: row for row in HISTORICAL["corpora"]}
        for code in ("eye", "czech-television"):
            item = by_code[code]
            self.assertEqual(item["humanAccessEvidence"], "official_sample_observed")
            self.assertTrue(item["sampleSourceUrl"].startswith("https://"))
            self.assertEqual(item["recordDisplay"], "not_authorized_for_new_site")
        self.assertEqual(by_code["ape"]["humanAccessEvidence"], "portal_search_interface_observed")
        self.assertEqual(by_code["ciclic"]["humanAccessEvidence"], "environment_limited")
        self.assertEqual(by_code["ape"]["rightsAssessment"], "hold_reclassify_external_media_inventory")
        self.assertEqual(by_code["europeana"]["rightsAssessment"], "hold_scientific_and_item_source_review")
        self.assertIn("16 repetições", by_code["ape"]["reviewReason"])
        self.assertIn("7 com tipo audiovisual", by_code["europeana"]["reviewReason"])
        for code in ("ape", "ciclic", "barch", "asim", "bnfa"):
            self.assertEqual(by_code[code]["recordDisplay"], "not_authorized_for_new_site")

    def test_web_routes_and_migration_are_static(self):
        page = (SITE / "app/(pt)/indice-acesso/page.tsx").read_text(encoding="utf-8")
        component = (SITE / "components/public-access-inventory.tsx").read_text(encoding="utf-8")
        nav = (SITE / "components/site-header.tsx").read_text(encoding="utf-8")
        self.assertIn('"/indice-acesso/"', nav)
        self.assertIn("PublicAccessInventory", page)
        self.assertIn("copy.accessReasonLead", component)
        self.assertIn("copy.accessPublicationHold", component)
        self.assertIn("ScientificText", page)
        self.assertIn("copy.accessVisitorLead", component)
        self.assertIn("item.humanAccessNote", component)
        self.assertIn("corpus.restrictionEvidence", component)
        self.assertIn("public-access-observatory.json", component)
        for code in (page, component):
            for unsafe in ("<iframe", "<video", "fetch(", "DATABASE_URL", "psycopg"):
                self.assertNotIn(unsafe, code)


if __name__ == "__main__":
    unittest.main()
