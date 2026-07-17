import unittest

from memoria_audiovisual.filmarchiv_austria import (
    collect_filmarchiv_austria_dataset,
    parse_filmarchiv_austria_detail,
    parse_filmarchiv_austria_listing,
)


LISTING_HTML = """
<main>
  <a href="/de/filmarchiv-on/video/f_test001">1926 16:37 Die Eröffnung des Thermalbades</a>
  <a href="/de/filmarchiv-on/video/f_test001">Die Eröffnung des Thermalbades</a>
  <a href="/de/filmarchiv-on/video/f_test002">1983 79 min Angst verfügbar bis 30.7.2026</a>
</main>
"""

DETAIL_HTML = """
<main>
  <a href="/de/filmarchiv-on">ON</a>
  <a href="/de/filmarchiv-on/historische-filmdokumente">Historische Filmdokumente</a>
  <span>➜ edit</span>
  <span>f_test001</span>
  <h1>Die Eröffnung des Thermalbades</h1>
  <p>Die Filmaufnahmen zeigen die Eröffnung des neu erbauten Thermalbades.</p>
  <p>Originaltitel:</p><p>Die Eröffnungsfeierlichkeiten</p>
  <p>Land:</p><p>Österreich</p>
  <p>Jahr:</p><p>1926</p>
  <p>Quelle:</p><p>35-mm-Nitropositiv, Sammlung Filmarchiv Austria</p>
  <p>Zurück</p>
</main>
"""


class FilmarchivAustriaCollectionTests(unittest.TestCase):
    def test_parse_listing_deduplicates_public_video_pages(self):
        records = parse_filmarchiv_austria_listing(LISTING_HTML)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["record_id"], "f_test001")
        self.assertIn("filmarchiv.at/de/filmarchiv-on/video/f_test001", records[0]["video_link"])

    def test_parse_detail_extracts_core_metadata(self):
        record = parse_filmarchiv_austria_detail(
            DETAIL_HTML,
            "https://www.filmarchiv.at/de/filmarchiv-on/video/f_test001",
            {"card_text": "1926 Die Eröffnung des Thermalbades"},
        )

        self.assertEqual(record["title"], "Die Eröffnung des Thermalbades")
        self.assertEqual(record["date"], "1926")
        self.assertIn("Österreich", record["subject"])
        self.assertIn("35-mm-Nitropositiv", record["description"])

    def test_collect_dataset_uses_injected_fetcher(self):
        detail_by_url = {
            "https://www.filmarchiv.at/de/filmarchiv-on": LISTING_HTML,
            "https://www.filmarchiv.at/de/filmarchiv-on/video/f_test001": DETAIL_HTML,
            "https://www.filmarchiv.at/de/filmarchiv-on/video/f_test002": DETAIL_HTML.replace(
                "f_test001", "f_test002"
            ).replace("1926", "1983"),
        }

        def fetch_html(url):
            return detail_by_url[url], url, 200

        institutions, summary, links, internal_pages = collect_filmarchiv_austria_dataset(fetch_html)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["video_links_found_total"], 2)
        self.assertEqual(len(links), 2)
        self.assertEqual(len(internal_pages), 3)
        self.assertTrue(all(row["platform"] == "Filmarchiv ON" for row in links))


if __name__ == "__main__":
    unittest.main()
