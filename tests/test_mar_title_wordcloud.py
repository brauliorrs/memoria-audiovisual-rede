"""Guardrails for derived title-term cloud, independent of media and ficha rights."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = json.loads((SITE / "data/title-wordcloud.json").read_text(encoding="utf-8"))


class HomepageTitleCloudTests(unittest.TestCase):
    def test_full_historical_input_and_published_aggregate_only(self):
        self.assertEqual(DATA["schema"], "mar-title-wordcloud-v1")
        self.assertGreaterEqual(DATA["corporaProcessed"], 63)
        self.assertGreaterEqual(DATA["titlesExamined"], 194696)
        self.assertGreaterEqual(DATA["distinctTitlesWithTerms"], 80000)
        self.assertEqual(DATA["titlesExamined"], sum(s["rows"] for s in DATA["sourceProvenance"]))
        self.assertEqual(DATA["distinctTitlesWithTerms"], sum(s["titlesWithTerms"] for s in DATA["sourceProvenance"]))
        self.assertFalse(DATA["rawTitlesPublished"])
        self.assertFalse(DATA["individualRecordsPublished"])
        self.assertEqual(len(DATA["sourceProvenance"]), DATA["corporaProcessed"])
        self.assertEqual(len({s["code"] for s in DATA["sourceProvenance"]}), DATA["corporaProcessed"])
        self.assertIn("kavi", {s["code"] for s in DATA["sourceProvenance"]})
        self.assertTrue(all(len(s["sha256"]) == 64 for s in DATA["sourceProvenance"]))

    def test_cloud_keeps_only_frequent_cross_corpus_terms(self):
        items = DATA["words"]
        self.assertGreaterEqual(len(items), 18)
        self.assertLessEqual(len(items), 38)
        self.assertEqual(len(set(w["text"] for w in items)), len(items))
        self.assertTrue(all(w["count"] >= 20 and w["corpora"] >= 2 for w in items))
        self.assertTrue(all(4 <= len(w["text"]) <= 23 for w in items))
        self.assertEqual([w["score"] for w in items],
                         sorted((w["score"] for w in items), reverse=True))
        for item in items:
            self.assertNotIn("http", item["text"])
            self.assertNotIn("<", item["text"])
            self.assertNotIn(">", item["text"])
        self.assertTrue(all(set(item) == {"text", "count", "corpora", "score"} for item in items))

    def test_cloud_replaces_old_decorative_hero(self):
        page = (SITE / "app/page.tsx").read_text(encoding="utf-8")
        component = (SITE / "components/title-wordcloud.tsx").read_text(encoding="utf-8")
        css = (SITE / "app/globals.css").read_text(encoding="utf-8")
        self.assertIn("<TitleWordCloud />", page)
        self.assertNotIn("orbit-label-one", page)
        self.assertNotIn('aria-hidden="true">\n            <div className="orbit', page)
        self.assertIn("titleTerms.words", component)
        self.assertIn("formatter.format(term.count)", component)
        self.assertIn("title-cloud-words", css)
        for dangerous in ("<iframe", "<video", "fetch(", "DATABASE_URL", "window.location", "api.finna.fi"):
            self.assertNotIn(dangerous, component)

    def test_approved_kavi_catalogue_is_valid(self):
        kavi = json.loads((SITE / "data/kavi-public.json").read_text(encoding="utf-8"))
        self.assertEqual(kavi["total"], len(kavi["records"]))
        self.assertTrue(kavi["approvedMetadataPublication"])
        self.assertFalse(kavi["mediaPlaybackVerified"])


if __name__ == "__main__":
    unittest.main()
