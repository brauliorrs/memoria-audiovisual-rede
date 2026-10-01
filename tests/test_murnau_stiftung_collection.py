import unittest

from memoria_audiovisual.murnau_stiftung import (
    collect_murnau_stiftung_institutions,
    parse_murnau_detail_page,
    parse_murnau_search_page,
)

SEARCH_HTML = """
<html><body><h2>2 Suchergebnisse</h2>
<a href="/movie/674">Nosferatu</a>
<a href="/movie/31">Die Austreibung</a>
<a href="/movie/674">Nosferatu duplicate</a>
</body></html>
"""

DETAIL_HTML = """
<html><body>
<h2>Nosferatu</h2>
<p>(Spielfilm/Hauptfilm)</p>
<ul>
<li>Horrorfilm aus dem Jahre 1921</li>
<li>Länge: 1742m 64min</li>
<li>Land: Deutschland</li>
<li>Regie: Friedrich Wilhelm Murnau</li>
<li>Drehbuch: Henrik Galeen</li>
</ul>
<p>Produktion: Prana Film GmbH</p>
</body></html>
"""


class MurnauStiftungCollectionTests(unittest.TestCase):
    def test_institution_contract(self):
        row = collect_murnau_stiftung_institutions()[0]
        self.assertEqual(row["institution"], "Friedrich-Wilhelm-Murnau-Stiftung")
        self.assertEqual(row["country"], "Germany")
        self.assertTrue(row["content_available_in_source"])

    def test_search_parser_deduplicates_movie_ids(self):
        declared, rows = parse_murnau_search_page(
            SEARCH_HTML,
            "https://www.murnau-stiftung.de/movie_search?year=1921",
        )
        self.assertEqual(declared, 2)
        self.assertEqual([row["record_id"] for row in rows], ["674", "31"])
        self.assertEqual(rows[0]["title"], "Nosferatu")

    def test_detail_parser_extracts_core_metadata(self):
        row = parse_murnau_detail_page(
            DETAIL_HTML,
            "https://www.murnau-stiftung.de/movie/674",
        )
        self.assertEqual(row["record_id"], "674")
        self.assertEqual(row["title"], "Nosferatu")
        self.assertEqual(row["date"], "1921")
        self.assertIn("Friedrich Wilhelm Murnau", row["subject"])
        self.assertIn("Deutschland", row["description"])
        self.assertFalse(row["embedded"])


if __name__ == "__main__":
    unittest.main()
