import unittest

from memoria_audiovisual.config import EUROPEAN_FILM_GATEWAY_HOME_URL
from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.efg import (
    collect_european_film_gateway_institutions,
    parse_efg_video_items,
)


class EuropeanFilmGatewayCollectionTests(unittest.TestCase):
    def test_collect_efg_institutions_declares_single_aggregator(self):
        institutions = collect_european_film_gateway_institutions()

        self.assertEqual(len(institutions), 1)
        record = institutions[0]
        self.assertEqual(record["institution"], "European Film Gateway")
        self.assertEqual(record["external_url"], EUROPEAN_FILM_GATEWAY_HOME_URL)
        self.assertEqual(record["efg_detail_url"], EUROPEAN_FILM_GATEWAY_HOME_URL)
        self.assertTrue(record["content_available_in_source"])
        self.assertEqual(record["archive_type"], "European film and audiovisual aggregator")

    def test_parse_efg_video_items_detects_video_context(self):
        html = """
        <html><body>
        <div class="item"><a href="/detail/example-1">Vater ist im Kriege</a> video | 577 views</div>
        <div class="item"><a href="/about">About</a></div>
        </body></html>
        """

        records = parse_efg_video_items(html, "https://www.europeanfilmgateway.eu/", query="film")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Vater ist im Kriege")
        self.assertEqual(records[0]["query"], "film")

    def test_efg_urls_are_classified_as_european_audiovisual_surface(self):
        item_url = "https://www.europeanfilmgateway.eu/detail/example-1"

        self.assertEqual(classify_platform(item_url), "European Film Gateway")
        self.assertTrue(is_probably_video_link(item_url, "European Film Gateway"))
        self.assertEqual(
            classify_access_surface({"platform": "European Film Gateway", "video_link": item_url}),
            "Agregador audiovisual europeu especializado em cinema",
        )


if __name__ == "__main__":
    unittest.main()
