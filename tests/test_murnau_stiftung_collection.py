import unittest

from memoria_audiovisual.murnau_stiftung import (
    MURNAU_STIFTUNG_END_YEAR,
    MURNAU_STIFTUNG_START_YEAR,
    collect_murnau_stiftung_dataset,
    parse_murnau_detail_page,
    parse_murnau_search_page,
)


SEARCH_1921 = """
<html><body>
<h2>2 Suchergebnisse</h2>
<a href="/movie/674">Nosferatu</a>
<a href="/movie/674">Nosferatu duplicate navigation</a>
<a href="/movie/999">Testfilm</a>
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

HOLDINGS_HTML = """
<html><body>
<p>Der Filmstock umfasst mehr als 6.000 Stumm- und Tonfilme.</p>
</body></html>
"""


class FakeResponse:
    def __init__(self, text, url, status_code=200):
        self.text = text
        self.url = url
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class MurnauStiftungCollectionTests(unittest.TestCase):
    def test_search_parser_deduplicates_ids_and_checks_declared_total(self):
        rows, total = parse_murnau_search_page(
            SEARCH_1921,
            "https://www.murnau-stiftung.de/movie_search?year=1921",
            query_year="1921",
        )
        self.assertEqual(total, 2)
        self.assertEqual([row["record_id"] for row in rows], ["674", "999"])
        self.assertEqual(rows[0]["title"], "Nosferatu")
        self.assertEqual(rows[0]["date"], "1921")
        self.assertEqual(
            rows[0]["page_url"],
            "https://www.murnau-stiftung.de/movie/674",
        )

    def test_detail_parser_extracts_core_metadata(self):
        row = parse_murnau_detail_page(
            DETAIL_HTML,
            "https://www.murnau-stiftung.de/movie/674",
        )
        self.assertEqual(row["record_id"], "674")
        self.assertEqual(row["title"], "Nosferatu")
        self.assertEqual(row["date"], "1921")
        self.assertIn("Friedrich Wilhelm Murnau", row["director"])
        self.assertIn("Prana Film", row["production"])
        self.assertIn("64min", row["length"])

    def test_collector_can_materialize_year_partitioned_catalog_without_details(self):
        def robots_checker(_url):
            return True, "robots_evaluated"

        def fetch(url):
            if url.endswith("/filmbestand"):
                return FakeResponse(HOLDINGS_HTML, url)
            if "year=1921" in url:
                return FakeResponse(SEARCH_1921, url)
            return FakeResponse("<html><body><h2>0 Suchergebnisse</h2></body></html>", url)

        institutions, summary, links, internal = collect_murnau_stiftung_dataset(
            fetch=fetch,
            robots_checker=robots_checker,
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 2)
        self.assertEqual(len(links), 2)
        self.assertEqual(
            len(internal),
            1 + (MURNAU_STIFTUNG_END_YEAR - MURNAU_STIFTUNG_START_YEAR + 1),
        )
        self.assertTrue(
            all(row["platform"] == "Murnau-Stiftung Filmsuche" for row in links)
        )

    def test_collector_fails_closed_when_robots_is_not_verifiable(self):
        institutions, summary, links, internal = collect_murnau_stiftung_dataset(
            fetch=lambda _url: self.fail("fetch must not run"),
            robots_checker=lambda _url: (False, "robots_unreachable"),
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(links, [])
        self.assertEqual(summary[0]["status"], "sem_registros")
        self.assertEqual(summary[0]["error"], "robots_unreachable")
        self.assertEqual(internal[0]["status"], "bloqueado_robots")


if __name__ == "__main__":
    unittest.main()
