import json
import unittest

from memoria_audiovisual.asim import parse_asim_detail_page, parse_asim_search_page


class AsimCollectionTest(unittest.TestCase):
    def test_parse_asim_search_page_keeps_only_asim_details(self):
        html = """
        <a href="/detail/Film A/asim::abc">Details</a>
        <a href="/detail/Film A/asim::abc">Details</a>
        <a href="/detail/Other/provider::xyz">Details</a>
        """
        links = parse_asim_search_page(html, "https://www.europeanfilmgateway.eu/search-efg/example")
        self.assertEqual(links, ["https://www.europeanfilmgateway.eu/detail/Film A/asim::abc"])

    def test_parse_asim_detail_page_extracts_metadata_and_player(self):
        setup = json.dumps(
            {
                "sources": [
                    {
                        "type": "video/vimeo",
                        "src": "https://vimeo.com/123",
                    }
                ]
            }
        )
        html = f"""
        <h1>La festa</h1>
        <video data-setup='{setup}'></video>
        <a href="https://memoirefilmiquedusud.eu/idurl/1/1">View at Mémoire filmique Pyrénées-Méditerranée</a>
        <div>
          Genre:
          Documentary film
          Year:
          1915
          Runtime:
          00:10:00
          Description:
          Registro documental.
          Keywords:
          Mallorca / festa
          Provider:
          Arxiu del So i de la Imatge de Mallorca
          Rights:
          Public Domain
        </div>
        """
        record = parse_asim_detail_page(
            html,
            "https://www.europeanfilmgateway.eu/detail/La%20festa/asim::abc",
        )
        self.assertEqual(record["record_id"], "abc")
        self.assertEqual(record["title"], "La festa")
        self.assertEqual(record["media_source_url"], "https://vimeo.com/123")
        self.assertEqual(record["genre"], "Documentary film")
        self.assertEqual(record["year"], "1915")
        self.assertTrue(record["has_public_player"])
        self.assertIn("Registro documental", record["description"])


if __name__ == "__main__":
    unittest.main()
