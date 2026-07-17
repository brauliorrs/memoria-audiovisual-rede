import unittest

from memoria_audiovisual.config import FILMMUSEUM_DUSSELDORF_ARCHIVE_URL
from memoria_audiovisual.filmmuseum_dusseldorf import (
    collect_filmmuseum_dusseldorf_dataset,
    parse_dkult_object_detail,
    parse_dkult_object_links,
)


LISTING_HTML = """
<section>
  <a href="/objects/348865/bitte-steigen-sie-ein">Bitte steigen Sie ein</a>
  <a href="/objects/348865/bitte-steigen-sie-ein">Duplikat</a>
  <a href="/objects/348866/dusseldorf-im-film">Düsseldorf im Film</a>
</section>
"""

DETAIL_HTML = """
<main>
  <h1>Bitte steigen Sie ein</h1>
  <div class="detailField">
    <span class="detailFieldLabel">Objektnummer</span>
    <span class="detailFieldValue">FM-001</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Datierung</span>
    <span class="detailFieldValue">1962</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Klassifikation(en)</span>
    <span class="detailFieldValue">Ton/bewegtes Bild - Werk</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Filmgenre</span>
    <span class="detailFieldValue">Dokumentarfilm</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Schlagwort Film</span>
    <span class="detailFieldValue">Rheinbahn</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Dargestellter Ort</span>
    <span class="detailFieldValue">Düsseldorf</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Produktionsland</span>
    <span class="detailFieldValue">Deutschland</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Regie</span>
    <span class="detailFieldValue">Erika Muster</span>
  </div>
  <div class="detailField">
    <span class="detailFieldLabel">Beschreibung</span>
    <span class="detailFieldValue">Film über Verkehr und Alltag in Düsseldorf.</span>
  </div>
</main>
"""


class FilmmuseumDusseldorfCollectionTests(unittest.TestCase):
    def test_parse_links_deduplicates_dkult_objects(self):
        records = parse_dkult_object_links(
            LISTING_HTML,
            "https://emuseum.duesseldorf.de/collections/56457/audiovisuelle-dokumente-zu-dusseldorf/objects/images?page=1",
        )

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["object_id"], "348865")
        self.assertIn("emuseum.duesseldorf.de/objects/348865", records[0]["object_url"])

    def test_parse_detail_extracts_core_metadata(self):
        record = parse_dkult_object_detail(
            DETAIL_HTML,
            "https://emuseum.duesseldorf.de/objects/348865/bitte-steigen-sie-ein",
        )

        self.assertEqual(record["title"], "Bitte steigen Sie ein")
        self.assertEqual(record["date"], "1962")
        self.assertIn("Ton/bewegtes Bild - Werk", record["subject"])
        self.assertIn("Rheinbahn", record["subject"])
        self.assertIn("player público de vídeo", record["description"])

    def test_collect_dataset_uses_public_ajax_route(self):
        detail_by_url = {
            "https://emuseum.duesseldorf.de/objects/348865/bitte-steigen-sie-ein": DETAIL_HTML,
            "https://emuseum.duesseldorf.de/objects/348866/dusseldorf-im-film": DETAIL_HTML.replace(
                "Bitte steigen Sie ein", "Düsseldorf im Film"
            ).replace("FM-001", "FM-002"),
        }
        ajax_calls = []

        def fetch_html(url, ajax=False):
            if url == FILMMUSEUM_DUSSELDORF_ARCHIVE_URL:
                return "<main><video src='demo.mp4'></video></main>", url, 200
            if "objects/images?page=1" in url:
                return LISTING_HTML, url, 200
            if "objects/images?page=2" in url:
                ajax_calls.append(ajax)
                return "<section></section>", url, 200
            return detail_by_url[url], url, 200

        institutions, summary, links, internal_pages = collect_filmmuseum_dusseldorf_dataset(fetch_html)

        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["video_links_found_total"], 2)
        self.assertEqual(len(links), 2)
        self.assertEqual(len(internal_pages), 5)
        self.assertEqual(ajax_calls, [True])
        self.assertTrue(all(row["platform"] == "d:kult online" for row in links))


if __name__ == "__main__":
    unittest.main()
