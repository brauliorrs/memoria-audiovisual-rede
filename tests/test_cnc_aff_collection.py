import unittest

from memoria_audiovisual.analysis import infer_video_theme
from memoria_audiovisual.cnc_aff import (
    collect_cnc_aff_institutions,
    extract_cnc_aff_result_total,
    parse_cnc_aff_detail_page,
    parse_cnc_aff_search_page,
)


class CncAffCollectionTests(unittest.TestCase):
    def test_collect_cnc_aff_institutions_declares_french_film_archive(self):
        institutions = collect_cnc_aff_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "FR-CNC-AFF")
        self.assertEqual(institutions[0]["country"], "France")

    def test_parse_cnc_aff_search_page_extracts_cnc_detail_links(self):
        html = """
        <main>
          <p>Videos (141 Results)</p>
          <a href="/detail/Fete nationale en Alsace/cnc::abc">Details</a>
          <a href="/detail/Other/bnfa::ignored">Details</a>
          <a href="/detail/Fete nationale en Alsace/cnc::abc">Details</a>
        </main>
        """

        links = parse_cnc_aff_search_page(
            html,
            "https://www.europeanfilmgateway.eu/search-efg/Centre%20nationale%20du%20cin%C3%A9ma%20CNC",
        )

        self.assertEqual(extract_cnc_aff_result_total(html), 141)
        self.assertEqual(len(links), 1)
        self.assertIn("cnc::abc", links[0])

    def test_parse_cnc_aff_detail_page_extracts_metadata(self):
        html = """
        <html>
          <body>
            <h1>Le Défilé de la victoire</h1>
            <div class="video-js">To view this video please enable JavaScript.</div>
            <dl>
              <dt>Other title(s):</dt><dd>The Victory Parade</dd>
              <dt>Genre:</dt><dd>Newsreel</dd>
              <dt>Year:</dt><dd>1919</dd>
              <dt>Description:</dt><dd>Allied troops march through Paris.</dd>
              <dt>Provider:</dt><dd>Centre nationale du cinéma et de l'image animée</dd>
            </dl>
          </body>
        </html>
        """

        record = parse_cnc_aff_detail_page(
            html,
            "https://www.europeanfilmgateway.eu/detail/Le Défilé de la victoire/cnc::abc",
        )
        analytic_row = {
            "platform": "European Film Gateway",
            "video_title": record["title"],
            "video_subject": record["genre"],
            "video_description": record["description"],
        }

        self.assertEqual(record["record_id"], "abc")
        self.assertEqual(record["title"], "Le Défilé de la victoire")
        self.assertEqual(record["genre"], "Newsreel")
        self.assertEqual(record["year"], "1919")
        self.assertTrue(record["has_player_shell"])
        self.assertEqual(infer_video_theme(analytic_row), "Cinejornal e atualidades")


if __name__ == "__main__":
    unittest.main()
