"""Internationalization only translates MAR UI, never changes the publication gate."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
KAVI=json.loads((SITE/"data/kavi-public.json").read_text(encoding="utf-8"))
INDEX=json.loads((SITE/"data/public-access-observatory.json").read_text(encoding="utf-8"))

class CatalogAndAccessI18n(unittest.TestCase):
    def test_approved_items_and_historical_inventory_remain_separate(self):
        self.assertEqual(KAVI["total"],200)
        self.assertEqual(len(KAVI["records"]),200)
        self.assertTrue(KAVI["approvedMetadataPublication"])
        self.assertFalse(KAVI["mediaPlaybackVerified"])
        self.assertFalse(KAVI["mediaRightsVerified"])
        self.assertEqual(len(INDEX["corpora"]),63)
        self.assertEqual(INDEX["kaviSiteApprovedRecords"],200)
        self.assertEqual(INDEX["summary"]["historicalMaterializedTotal"],194057)
        self.assertTrue(INDEX["publicationOfIndividualRecordsNotAuthorizedByThisFile"])
        self.assertTrue(all(c["recordDisplay"]=="not_authorized_for_new_site" for c in INDEX["corpora"]))

    def test_catalog_controls_use_site_locale_without_filtering_extra_items(self):
        content=(SITE/"components/catalog-search.tsx").read_text(encoding="utf-8")
        for term in (
            "useScientificCopy", "useSiteLocale", "copy.catalogSearchLabel",
            "copy.catalogPeriod", "copy.catalogTopicGenre", "copy.catalogSort",
            "copy.catalogSearchPlaceholder", "copy.catalogMetadataNotice",
            "copy.catalogMoreRecords", "copy.catalogViewLabel",
            'id="mar-search"', 'id="mar-decade"', 'id="mar-topic"',
            'id="mar-order"', 'aria-live="polite"',
            '"all"', "setLimit(PAGE_SIZE)", "items.filter",
            '"/acervo/kavi/" + encodeURIComponent(item.id)',
        ):
            self.assertIn(term,content,term)
        self.assertNotIn("new Intl.NumberFormat(\"pt-BR\").format", content)
        for forbidden in ("DATABASE_URL","<video","<iframe","fetch(","dangerouslySetInnerHTML","window.location"):
            self.assertNotIn(forbidden,content)

    def test_index_controls_still_show_original_source_evidence(self):
        page=(SITE/"app/indice-acesso/page.tsx").read_text(encoding="utf-8")
        content=(SITE/"components/public-access-inventory.tsx").read_text(encoding="utf-8")
        for term in ("ScientificText","ScientificNumber","summary.historicalMaterializedTotal",
                     "summary.historicalPublicSurfaceRecords",
                     "summary.historicalRestrictedRecords",
                     "inventory.kaviSiteApprovedRecords"):
            self.assertIn(term,page)
        for term in ("useScientificCopy", "copy.accessReasonLead",
                     "copy.accessVisitorLead", "copy.accessPublicationHold",
                     "copy.accessPublicRecords", "copy.accessRestrictedRecords",
                     "copy.accessFallbackPublic", "copy.accessFallbackUnquantified",
                     "corpus.restrictionEvidence", "item.humanAccessNote",
                     "item.sampleSourceUrl", "item.rightsPolicyUrl", 
                     "item.accessCategory", "item.historicalTotal === 0",
                     "fmt(item.historicalPublicSurfaceRecords)",
                     "fmt(item.historicalRestrictedRecords)"):
            self.assertIn(term,content,term)
        self.assertNotIn('toLocaleString("pt-BR")',content)
        for source in (page,content):
            for forbidden in ("DATABASE_URL","<video","<iframe","fetch(","psycopg"):
                self.assertNotIn(forbidden,source)

    def test_language_dictionary_has_all_required_keys(self):
        dictionary=(SITE/"components/scientific-i18n.tsx").read_text(encoding="utf-8")
        for key in ("catalogMoreRecords","catalogFoundMany","catalogMetadataNotice",
                    "accessPublicationHold","accessFootnoteAfter","accessOriginalNote",
                    "accessFallbackUnquantified","accessNewFiches"):
            self.assertGreaterEqual(dictionary.count(key+":"),3,key)

if __name__=="__main__":
    unittest.main()
