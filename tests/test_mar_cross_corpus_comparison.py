"""MAR multi-corpus scientific comparison: metadata scope, source coverage, and UI contracts."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"site"
PARTS=[json.loads((SITE/f"data/research-slices-{i}.json").read_text(encoding="utf-8")) for i in range(16)]
SOURCES={k:v for part in PARTS for k,v in part.items()}


class CrossCorpusComparisonTests(unittest.TestCase):
    def test_observational_sources_and_dimensions_are_reused(self):
        self.assertGreaterEqual(len(SOURCES),60)
        self.assertEqual(len(SOURCES),len(set(SOURCES)))
        for code,scope in SOURCES.items():
            self.assertTrue(code)
            self.assertEqual(set(scope),{"tema_pais","tema_plataforma","linha_do_tempo_corpus"})
            for dimension in scope.values():
                self.assertTrue(dimension["source"].startswith("data/output/"))
                self.assertTrue(dimension["source"].endswith(".csv"))
                self.assertIsInstance(dimension["rows"],list)
                for row in dimension["rows"]:
                    self.assertIsInstance(row,dict)
                    self.assertNotIn("video_title",row)
                    self.assertNotIn("video_url",row)
                    self.assertNotIn("media_url",row)
                    self.assertNotIn("work_id",row)

    def test_example_sources_have_real_independent_history(self):
        for code in ("ape","eye","europeana"):
            self.assertIn(code,SOURCES)
            source=SOURCES[code]
            self.assertTrue(source["tema_pais"]["rows"])
            self.assertTrue(source["tema_plataforma"]["rows"])
            self.assertTrue(source["linha_do_tempo_corpus"]["rows"])
            for row in source["tema_pais"]["rows"][:12]:
                self.assertIn("tema",row)
                self.assertIn("pais",row)
                self.assertGreaterEqual(int(row["total"]),0)

    def test_comparison_is_independent_per_source_with_no_raw_media(self):
        helper=(SITE/"lib/corpus-comparison.ts").read_text(encoding="utf-8")
        ui=(SITE/"components/corpus-comparison.tsx").read_text(encoding="utf-8")
        page=(SITE/"app/(pt)/comparar/page.tsx").read_text(encoding="utf-8")
        self.assertIn("compareDimensions",helper)
        self.assertIn("new Set(codes)",helper)
        self.assertIn(".slice(0, 3)",helper)
        self.assertIn("source.total",helper)
        self.assertIn("historicalSeries",helper)
        self.assertIn("chronologicalObservations",helper)
        self.assertIn("csvCell",helper)
        self.assertIn("toCsv",ui)
        self.assertIn("new Blob(",ui)
        self.assertIn("onClick={exportAggregate}",ui)
        self.assertIn("useSiteLocale",ui)
        self.assertIn("CorpusComparison",page)
        self.assertTrue(all(code in ui for code in ('pt:', 'en:', 'es:')))
        for forbidden in ("api.finna.fi", "DATABASE_URL", "<iframe", "<video", "video_title",
                          "video_url", "media_url", "catalogo_videos_analitico", "fetch("):
            self.assertNotIn(forbidden,ui)

    def test_site_navigation_discovery_and_canonical_site(self):
        pages=["site/components/site-header.tsx","site/app/(pt)/analises/page.tsx","site/app/(pt)/observatorio/page.tsx","site/app/(pt)/page.tsx"]
        for path in pages:
            self.assertIn("/comparar/",(ROOT/path).read_text(encoding="utf-8"))
        self.assertNotIn("mar-new-site",(SITE/"app/(pt)/comparar/page.tsx").read_text(encoding="utf-8"))
        self.assertEqual(json.loads((SITE/"data/kavi-public.json").read_text(encoding="utf-8"))["total"],200)


if __name__=="__main__":
    unittest.main()
