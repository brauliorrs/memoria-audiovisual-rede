"""Guardrails for the APE/Europeana per-record documentary review (offline only)."""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/audit_mar_ape_europeana_records.py"
spec = importlib.util.spec_from_file_location("mar_ape_europeana_review", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class RecordReviewTests(unittest.TestCase):
    def test_historical_corpora_reviewed_in_full_without_publication(self):
        for code, count in (("europeana", 20), ("ape", 412)):
            result = module.audit(code)
            self.assertEqual(result["rowsAudited"], count)
            self.assertEqual(len(result["records"]), count)
            self.assertFalse(result["publicationAllowed"])
            self.assertTrue(result["sourceSha256"])
            for row in result["records"]:
                self.assertFalse(row["publicationApproved"])
                self.assertFalse(row["scientificallyApproved"])
                self.assertFalse(row["mediaRightsVerified"])
                self.assertFalse(row["currentPageVerified"])
                self.assertGreaterEqual(row["csvLine"], 2)

    def test_europeana_item_identifiers_not_licenses_for_objects(self):
        report = module.audit("europeana")
        self.assertEqual(report["uniqueExactLinks"], 20)
        self.assertTrue(all(r["sourceItemIdentifier"] for r in report["records"]))
        self.assertTrue(all(r["urlHost"] == "www.europeana.eu" for r in report["records"]))
        self.assertTrue(all(r["metadataLicencePolicy"].startswith("CC0") for r in report["records"]))
        self.assertIn("object_rights_require_independent_review", report["issues"])
        self.assertIn("audiovisual_type_not_proven", report["issues"])

    def test_ape_institutional_index_not_archival_item_metadata(self):
        report = module.audit("ape")
        self.assertEqual(report["rowsAudited"], 412)
        self.assertGreater(report["duplicatesExactExtraRows"], 0)
        self.assertEqual(report["issues"]["third_party_media_not_ape_metadata"], 412)
        self.assertEqual(report["issues"]["no_ape_archival_item_identifier"], 412)
        self.assertTrue(all(r["sourceItemIdentifier"] is None for r in report["records"]))
        self.assertTrue(all(r["recordKind"] == "third_party_media_link" for r in report["records"]))
        self.assertTrue(all(r["institutionIdentifier"] for r in report["records"]))

    def test_identity_and_rights_parsing(self):
        self.assertEqual(module.european_item_id("https://www.europeana.eu/en/item/499/ABC"), "499/ABC")
        self.assertIsNone(module.european_item_id("https://youtube.com/embed/ABC"))
        self.assertEqual(module.video_identity("https://www.youtube.com/embed/abc?si=one"), "youtube:abc")
        self.assertEqual(module.video_identity("https://www.youtube.com/embed/abc?si=two"), "youtube:abc")
        self.assertEqual(module.rights_category("direitos: © provider"), "object_copyright_or_restriction_claim")
        self.assertEqual(module.rights_category("direitos: "), "object_rights_not_recorded")


if __name__ == "__main__":
    unittest.main()
