"""Scientific MAR PT/EN/ES migration keeps raw source labels and HOLD boundaries."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"

class ScientificI18nTests(unittest.TestCase):
    def test_scientific_pages_use_central_locale_dictionary(self):
        dictionary=(SITE/"components/scientific-i18n.tsx").read_text(encoding="utf-8")
        self.assertIn('"use client"', dictionary)
        self.assertIn("useSiteLocale()", dictionary)
        self.assertIn("scientificCopy", dictionary)
        self.assertIn("ScientificText", dictionary)
        for page in [
            "app/(pt)/observatorio/page.tsx",
            "app/(pt)/analises/page.tsx",
            "app/(pt)/metodologia/page.tsx",
            "app/(pt)/casos/page.tsx",
            "app/(pt)/acervo/page.tsx",
            "app/(pt)/observatorio/[code]/page.tsx",
            "app/(pt)/instituicoes/pesquisa/[source]/[entry]/page.tsx",
        ]:
            content=(SITE/page).read_text(encoding="utf-8")
            self.assertIn("ScientificText",content,page)
        for client in [
            "components/scientific-dashboard.tsx",
            "components/analytics-comparison.tsx",
            "components/corpus-historical-analytics.tsx",
            "components/documented-cases.tsx",
        ]:
            content=(SITE/client).read_text(encoding="utf-8")
            self.assertIn("useScientificCopy",content,client)
        self.assertIn("localizeTerritory",dictionary)

    def test_historical_snapshot_and_access_restrictions_unchanged(self):
        snapshot=json.loads((SITE/"data/public-access-observatory.json").read_text(encoding="utf-8"))
        public=json.loads((SITE/"data/kavi-public.json").read_text(encoding="utf-8"))
        self.assertEqual(len(snapshot["corpora"]),63)
        self.assertEqual(snapshot["summary"]["historicalMaterializedTotal"],194057)
        self.assertEqual(snapshot["kaviSiteApprovedRecords"],200)
        self.assertEqual(public["total"],200)
        self.assertFalse(public["mediaPlaybackVerified"])
        self.assertTrue(all(c["recordDisplay"]=="not_authorized_for_new_site" for c in snapshot["corpora"]))

    def test_no_source_mutation_or_content_republication_in_i18n(self):
        text=(SITE/"components/scientific-i18n.tsx").read_text(encoding="utf-8")
        forbidden=["<iframe","<video","fetch(","DATABASE_URL","api.finna.fi","window.localStorage","video_title"]
        for entry in forbidden:
            self.assertNotIn(entry,text)
        profile=(SITE/"app/(pt)/observatorio/[code]/page.tsx").read_text(encoding="utf-8")
        self.assertIn("corpus.humanAccessNote",profile)
        self.assertIn("corpus.reviewReason",profile)
        self.assertIn("corpus.rightsPolicyUrl",profile)
        self.assertIn("profSourceText",profile)

if __name__=="__main__":
    unittest.main()
