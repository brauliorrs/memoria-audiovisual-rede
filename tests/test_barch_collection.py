import unittest

from memoria_audiovisual.barch import (
    collect_barch_institutions,
    extract_barch_result_total,
    parse_barch_detail_page,
    parse_barch_search_page,
)


class BarchCollectionTests(unittest.TestCase):
    def test_collect_barch_institutions_declares_single_archive(self):
        institutions = collect_barch_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "DE-BArch")
        self.assertEqual(institutions[0]["country"], "Germany")

    def test_parse_barch_search_page_extracts_only_barch_detail_links(self):
        html = """
        <html>
          <body>
            <p>Videos (179 Results)</p>
            <a href="/detail/Vogesenwacht/barch::abc">Details</a>
            <a href="/detail/Die Straße/fwms::ignored">Details</a>
            <a href="/detail/Vogesenwacht/barch::abc">Details</a>
          </body>
        </html>
        """

        self.assertEqual(extract_barch_result_total(html), 179)
        links = parse_barch_search_page(html, "https://www.europeanfilmgateway.eu/search-efg/bundesarchiv")
        self.assertEqual(len(links), 1)
        self.assertIn("barch::abc", links[0])

    def test_parse_barch_detail_page_extracts_metadata_and_player_shell(self):
        html = """
        <html>
          <body>
            <h1>Vogesenwacht</h1>
            <div class="video-js">To view this video please enable JavaScript.</div>
            <dl>
              <dt>Genre:</dt><dd>Documentary</dd>
              <dt>Year:</dt><dd>1917</dd>
              <dt>Runtime:</dt><dd>00:04:42</dd>
              <dt>Description:</dt><dd>German wartime film record.</dd>
              <dt>Provider:</dt><dd>Bundesarchiv</dd>
              <dt>Rights:</dt><dd>In Copyright</dd>
            </dl>
          </body>
        </html>
        """

        record = parse_barch_detail_page(
            html,
            "https://www.europeanfilmgateway.eu/detail/Vogesenwacht/barch::abc",
        )

        self.assertEqual(record["record_id"], "abc")
        self.assertEqual(record["title"], "Vogesenwacht")
        self.assertEqual(record["genre"], "Documentary")
        self.assertEqual(record["year"], "1917")
        self.assertTrue(record["has_player_shell"])
        self.assertFalse(record["has_public_player"])
        self.assertIn("German wartime film record", record["description"])


if __name__ == "__main__":
    unittest.main()
