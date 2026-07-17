import unittest

from memoria_audiovisual.bnfa import (
    collect_bnfa_institutions,
    extract_bnfa_result_total,
    parse_bnfa_detail_page,
    parse_bnfa_search_page,
)


class BnfaCollectionTests(unittest.TestCase):
    def test_collect_bnfa_institutions_declares_single_archive(self):
        institutions = collect_bnfa_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "BG-BNFA")
        self.assertEqual(institutions[0]["country"], "Bulgaria")

    def test_parse_bnfa_search_page_extracts_bnfa_detail_links(self):
        html = """
        <html>
          <body>
            <p>Videos (168 Results)</p>
            <a href="/detail/ПРЕГЛЕДЪ 152/bnfa::abc">Details</a>
            <a href="/detail/Other/asim::ignored">Details</a>
            <a href="/detail/ПРЕГЛЕДЪ 152/bnfa::abc">Details</a>
          </body>
        </html>
        """

        self.assertEqual(extract_bnfa_result_total(html), 168)
        links = parse_bnfa_search_page(html, "https://www.europeanfilmgateway.eu/search-efg/bnfa")
        self.assertEqual(len(links), 1)
        self.assertIn("bnfa::abc", links[0])

    def test_parse_bnfa_detail_page_extracts_metadata_and_player_shell(self):
        html = """
        <html>
          <body>
            <h1>ПРЕГЛЕДЪ 152</h1>
            <div class="video-js">To view this video please enable JavaScript, and consider upgrading.</div>
            <dl>
              <dt>Other title(s):</dt><dd>NEWSREEL 152</dd>
              <dt>Genre:</dt><dd>Newsreel</dd>
              <dt>Year:</dt><dd>1944</dd>
              <dt>Runtime:</dt><dd>00:04:42</dd>
              <dt>Description:</dt><dd>The city of Burgas and a mineral water sanatorium.</dd>
              <dt>Provider:</dt><dd>Bulgarian National Film Archive</dd>
              <dt>Rights:</dt><dd>In Copyright - Educational Use Permitted</dd>
            </dl>
          </body>
        </html>
        """

        record = parse_bnfa_detail_page(
            html,
            "https://www.europeanfilmgateway.eu/detail/ПРЕГЛЕДЪ 152/bnfa::abc",
        )

        self.assertEqual(record["record_id"], "abc")
        self.assertEqual(record["title"], "ПРЕГЛЕДЪ 152")
        self.assertEqual(record["genre"], "Newsreel")
        self.assertEqual(record["year"], "1944")
        self.assertTrue(record["has_player_shell"])
        self.assertFalse(record["has_public_player"])
        self.assertIn("NEWSREEL 152", record["description"])


if __name__ == "__main__":
    unittest.main()
