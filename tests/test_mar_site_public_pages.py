"""Public MAR Next.js site contracts; no network or production systems."""
import json
import unittest
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
DATA = json.loads((SITE / "data/kavi-public.json").read_text(encoding="utf-8"))


class MarSitePublicPagesTests(unittest.TestCase):
    def test_exactly_200_unique_source_record_detail_routes(self):
        records = DATA["records"]
        self.assertEqual(len(records), 200)
        ids = [item["id"] for item in records]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len({item["sourceUrl"] for item in records}), 200)
        for item in records:
            self.assertNotIn("/", item["id"])
            self.assertNotIn("?", item["id"])
            url = urlparse(item["sourceUrl"])
            self.assertEqual(url.scheme, "https")
            self.assertEqual(url.netloc, "www.finna.fi")
            self.assertEqual(url.path, "/Record/" + item["id"])

    def test_static_route_preserves_metadata_and_scientific_disclosure(self):
        source = (SITE / "app/acervo/kavi/[id]/page.tsx").read_text(encoding="utf-8")
        self.assertIn("generateStaticParams", source)
        self.assertIn("records.map((record) => ({ id: record.id }))", source)
        self.assertIn("record.sourceUrl", source)
        self.assertIn("Não concluída", source)
        self.assertIn("Não verificados", source)
        self.assertIn("Não verificada", source)
        self.assertIn("publicIndex.catalogSha256", source)
        for forbidden in ("<video", "<iframe", "dangerouslySetInnerHTML", "fetch(", "psycopg", "DATABASE_URL"):
            self.assertNotIn(forbidden, source)

    def test_faceted_search_links_to_detail_pages(self):
        source = (SITE / "components/catalog-search.tsx").read_text(encoding="utf-8")
        self.assertIn('type="search"', source)
        self.assertIn("mar-decade", source)
        self.assertIn("mar-topic", source)
        self.assertIn("mar-order", source)
        self.assertIn("Mostrar mais fichas", source)
        self.assertIn('"/acervo/kavi/" + encodeURIComponent(item.id)', source)
        self.assertIn('aria-live="polite"', source)
        self.assertNotIn("window.location", source)

    def test_no_new_media_or_backend_access(self):
        self.assertTrue(DATA["approvedMetadataPublication"])
        self.assertFalse(DATA["individualReview"])
        self.assertFalse(DATA["mediaPlaybackVerified"])
        self.assertFalse(DATA["mediaRightsVerified"])
        self.assertEqual(DATA["scope"], "partial_metadata_only")
        self.assertNotIn("mar_corpora", (SITE / "lib/catalog.ts").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
