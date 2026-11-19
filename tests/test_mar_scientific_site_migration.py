"""Contract tests for the MAR scientific dashboard migration (snapshot-only)."""
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
INVENTORY=json.loads((SITE/"data/public-access-observatory.json").read_text(encoding="utf-8"))
CASES=json.loads((SITE/"data/documented-cases.json").read_text(encoding="utf-8"))
REPORTS=sum([json.loads((SITE/f"data/analytics-{i}.json").read_text(encoding="utf-8")) for i in range(6)],[])

class ScientificObservatoryTests(unittest.TestCase):
    def test_snapshot_totals_and_no_new_public_fiches(self):
        corpus=INVENTORY["corpora"]
        self.assertEqual(len(corpus),63)
        self.assertEqual(sum(c["historicalPublicSurfaceRecords"] for c in corpus),165134)
        self.assertEqual(sum(c["historicalRestrictedRecords"] for c in corpus),28923)
        self.assertEqual(sum(c["historicalTotal"] for c in corpus),194057)
        self.assertEqual(INVENTORY["kaviSiteApprovedRecords"],200)
        self.assertTrue(all(c["recordDisplay"]=="not_authorized_for_new_site" for c in corpus))
        self.assertEqual(len({c["code"] for c in corpus}),63)

    def test_documented_cases_migrated_without_record_publication(self):
        self.assertEqual(len(CASES["cases"]),17)
        self.assertFalse(CASES["publicationAuthorized"])
        self.assertEqual(len({c["code"] for c in CASES["cases"]}),17)
        self.assertTrue(all(c["name"] and c["reason"] and c["evidence"] for c in CASES["cases"]))

    def test_historical_analytical_reports_complete_and_private(self):
        self.assertEqual(len(REPORTS),62)
        self.assertEqual(len({r["code"] for r in REPORTS}),62)
        self.assertTrue(all(r["source"].startswith("data/output/") for r in REPORTS))
        self.assertTrue(all(r["totalInstitutions"]>=0 and r["institutionsWithVideo"]>=0 for r in REPORTS))
        self.assertTrue(any(r["code"]=="eye" and r["totalInstitutions"]==1 for r in REPORTS))
        self.assertTrue(any(r["code"]=="ape" and r["totalInstitutions"]>1000 for r in REPORTS))

    def test_scientific_routes_and_separation_from_public_catalog(self):
        dashboard=(SITE/"components/scientific-dashboard.tsx").read_text(encoding="utf-8")
        profile=(SITE/"app/(pt)/observatorio/[code]/page.tsx").read_text(encoding="utf-8")
        page=(SITE/"app/(pt)/observatorio/page.tsx").read_text(encoding="utf-8")
        cases=(SITE/"app/(pt)/casos/page.tsx").read_text(encoding="utf-8")
        nav=(SITE/"components/site-header.tsx").read_text(encoding="utf-8")
        analytics=(SITE/"app/(pt)/analises/page.tsx").read_text(encoding="utf-8")
        corpus_analytics=(SITE/"components/corpus-historical-analytics.tsx").read_text(encoding="utf-8")
        self.assertIn("generateStaticParams",profile)
        self.assertIn("63",str(len(INVENTORY["corpora"])))
        self.assertIn("ScientificDashboard",page)
        self.assertIn("DocumentedCases",cases)
        self.assertIn("/observatorio/",nav)
        self.assertIn("/casos/",nav)
        self.assertIn("/analises/",nav)
        self.assertIn("CorpusHistoricalAnalytics",profile)
        self.assertIn("historicalAnalyticReports",analytics)
        self.assertIn("rankSummary",corpus_analytics)
        self.assertIn("historicalPublicSurfaceRecords",dashboard)
        for code in (dashboard,profile,page,cases,analytics,corpus_analytics):
            for unsafe in ("fetch(", "DATABASE_URL", "<iframe", "<video", "api.finna.fi", "psycopg"):
                self.assertNotIn(unsafe,code)

if __name__=="__main__":
    unittest.main()
