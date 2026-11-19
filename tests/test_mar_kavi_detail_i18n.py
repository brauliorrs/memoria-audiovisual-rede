"""KAVI multilingual record details: source text unchanged and no new release gate."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
DATA=json.loads((SITE/"data/kavi-public.json").read_text(encoding="utf-8"))

class KaviRecordI18nTests(unittest.TestCase):
    def test_all_200_individual_static_routes_and_scope_are_unchanged(self):
        route=(SITE/"app/acervo/kavi/[id]/page.tsx").read_text(encoding="utf-8")
        detail=(SITE/"components/kavi-record-detail.tsx").read_text(encoding="utf-8")
        self.assertEqual(len(DATA["records"]),200)
        self.assertEqual(DATA["total"],200)
        self.assertEqual(len({r["id"] for r in DATA["records"]}),200)
        self.assertTrue(DATA["approvedMetadataPublication"])
        self.assertFalse(DATA["individualReview"])
        self.assertFalse(DATA["mediaPlaybackVerified"])
        self.assertFalse(DATA["mediaRightsVerified"])
        self.assertIn("generateStaticParams",route)
        self.assertIn("records.map((record) => ({ id: record.id }))",route)
        self.assertIn("record.title",route)
        self.assertIn("record={record}",route)
        self.assertIn("KaviRecordDetail",route)
        self.assertIn("approvedCatalogSha256={publicIndex.catalogSha256}",route)
        self.assertIn("observedOn={publicIndex.observedOn}",route)
        self.assertIn("record.sourceUrl",detail)
        self.assertIn("record.genres",detail)
        self.assertIn("record.subjects",detail)
        self.assertIn("record.languages",detail)
        self.assertIn("record.institution",detail)
        self.assertIn("record.country",detail)
        self.assertIn("record.source",detail)
        self.assertIn("record.year",detail)
        for text in (route,detail):
            for forbidden in ("<iframe","<video","dangerouslySetInnerHTML","DATABASE_URL","fetch(","psycopg"):
                self.assertNotIn(forbidden,text)

    def test_detail_editorial_translation_does_not_change_metadata(self):
        detail=(SITE/"components/kavi-record-detail.tsx").read_text(encoding="utf-8")
        dictionary=(SITE/"components/scientific-i18n.tsx").read_text(encoding="utf-8")
        for code in ("pt","en","es"):
            self.assertIn(code+": {",dictionary)
        for term in ("copy.kaviFieldId","copy.kaviFieldYear","copy.kaviFieldGenres",
                     "copy.kaviFieldSubjects","copy.kaviFieldLanguage","copy.kaviFieldInstitution",
                     "copy.kaviFieldCountry","copy.kaviFieldService",
                     "copy.kaviReviewStatus","copy.kaviPlaybackStatus",
                     "copy.kaviMediaRightsStatus","copy.kaviProvenancePill",
                     "copy.kaviOriginalMetadataNote","copy.kaviApprovedHash"):
            self.assertIn(term,detail)
        self.assertIn("useSiteLocale",detail)
        self.assertIn("useScientificCopy",detail)
        self.assertTrue((SITE/"tests/kavi-record-detail.test.cjs").exists())

    def test_historical_hold_corpora_stay_unpublished(self):
        history=json.loads((SITE/"data/public-access-observatory.json").read_text(encoding="utf-8"))
        self.assertEqual(len(history["corpora"]),63)
        self.assertTrue(all(c["recordDisplay"]=="not_authorized_for_new_site" for c in history["corpora"]))
        self.assertEqual(history["kaviSiteApprovedRecords"],200)

if __name__=="__main__":
    unittest.main()
