import unittest

from memoria_audiovisual.config import EUROPEANA_HOME_URL
from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.europeana import (
    _extract_item_id,
    collect_europeana_institutions,
    parse_europeana_search_results,
)


class EuropeanaCollectionTests(unittest.TestCase):
    def test_collect_europeana_institutions_declares_single_aggregator(self):
        institutions = collect_europeana_institutions()

        self.assertEqual(len(institutions), 1)
        record = institutions[0]
        self.assertEqual(record["institution"], "Europeana")
        self.assertEqual(record["external_url"], EUROPEANA_HOME_URL)
        self.assertEqual(record["europeana_detail_url"], EUROPEANA_HOME_URL)
        self.assertTrue(record["content_available_in_source"])
        self.assertEqual(record["archive_type"], "European cultural aggregator with audiovisual records")

    def test_extract_item_id_accepts_europeana_item_urls(self):
        self.assertEqual(
            _extract_item_id("https://www.europeana.eu/en/item/91660/SMVK_EM_video_3938240"),
            "91660/SMVK_EM_video_3938240",
        )

    def test_parse_europeana_search_results_detects_cards(self):
        html = """
        <html><body>
        5 results
        <div class="card-wrapper">
          <div class="card-title"><a class="card-link" href="/en/item/91660/SMVK_EM_video_3938240">- video -, video</a></div>
          <div class="card-text"><p>Schultz, Martin</p></div>
          <div class="card-text"><p>Museum of Ethnography</p></div>
        </div>
        </body></html>
        """

        records, result_count = parse_europeana_search_results(
            html,
            "https://www.europeana.eu/en/search?query=video&media=true",
            "video",
        )

        self.assertEqual(result_count, 5)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["provider"], "Museum of Ethnography")

    def test_europeana_urls_are_classified_as_cultural_aggregator_surface(self):
        item_url = "https://www.europeana.eu/en/item/91660/SMVK_EM_video_3938240"

        self.assertEqual(classify_platform(item_url), "Europeana")
        self.assertTrue(is_probably_video_link(item_url, "Europeana"))
        self.assertEqual(
            classify_access_surface({"platform": "Europeana", "video_link": item_url}),
            "Agregador cultural europeu com recorte audiovisual",
        )


if __name__ == "__main__":
    unittest.main()
