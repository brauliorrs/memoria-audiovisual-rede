import string
import unittest

from memoria_audiovisual.corpora import CORPORA
from memoria_audiovisual.europe_research import (
    build_europe_research_queue,
    build_europe_research_registry,
)
from memoria_audiovisual.inclusion_queue import select_inclusion_candidates
from memoria_audiovisual.murnau_stiftung import (
    MURNAU_STIFTUNG_ALPHA_LETTERS,
    MURNAU_STIFTUNG_MAX_DETAIL_PAGES,
    collect_murnau_stiftung_dataset,
    parse_murnau_alpha_page,
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

ALPHA_HTML = """
<html><body>
<div class="views-row">
  <a href="/movie/674">Nosferatu</a>
  <div>Produktionsjahr: 1921</div>
  <div>Erstaufführung: 04.03.1922</div>
</div>
<div class="views-row">
  <a href="/movie/999">Testfilm</a>
  <div>Produktionsjahr: 1931</div>
  <div>Erstaufführung: 01.01.1932</div>
</div>
<a href="/movie/674">duplicate navigation</a>
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


def synthetic_letter_page(letter, count=240):
    offset = (ord(letter) - ord("A") + 1) * 10000
    rows = []
    for index in range(count):
        record_id = offset + index
        year = 1900 + (index % 60)
        rows.append(
            f'<div class="views-row"><a href="/movie/{record_id}">'
            f'{letter} Film {index:03d}</a>'
            f'<div>Produktionsjahr: {year}</div>'
            f'<div>Erstaufführung: 01.01.{year}</div></div>'
        )
    return "<html><body>" + "".join(rows) + "</body></html>"


class MurnauStiftungCollectionTests(unittest.TestCase):
    def test_search_parser_remains_available_as_diagnostic(self):
        rows, total = parse_murnau_search_page(
            SEARCH_1921,
            "https://www.murnau-stiftung.de/movie_search?year=1921",
            query_year="1921",
        )
        self.assertEqual(total, 2)
        self.assertEqual([row["record_id"] for row in rows], ["674", "999"])
        self.assertEqual(rows[0]["date"], "1921")

    def test_alpha_parser_deduplicates_ids_and_extracts_year(self):
        rows = parse_murnau_alpha_page(
            ALPHA_HTML,
            "https://www.murnau-stiftung.de/list/movies/letter/N",
            letter="N",
        )
        self.assertEqual([row["record_id"] for row in rows], ["674", "999"])
        self.assertEqual(rows[0]["title"], "Nosferatu")
        self.assertEqual(rows[0]["date"], "1921")
        self.assertEqual(rows[0]["source_partition"], "N")
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

    def test_collector_requires_complete_alpha_partitions_and_holdings_floor(self):
        def robots_checker(_url):
            return True, "robots_evaluated"

        def fetch(url):
            if url.endswith("/filmbestand"):
                return FakeResponse(HOLDINGS_HTML, url)
            if "/list/movies/letter/" in url:
                letter = url.rstrip("/").rsplit("/", 1)[-1].upper()
                if letter not in string.ascii_uppercase:
                    raise AssertionError(url)
                return FakeResponse(synthetic_letter_page(letter), url)
            if "/movie/" in url:
                return FakeResponse(DETAIL_HTML, url)
            raise AssertionError(url)

        institutions, summary, links, internal = collect_murnau_stiftung_dataset(
            fetch=fetch,
            robots_checker=robots_checker,
        )
        self.assertEqual(len(institutions), 1)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 6240)
        self.assertEqual(len(links), 6240)
        self.assertEqual(
            len(internal),
            1 + len(MURNAU_STIFTUNG_ALPHA_LETTERS)
            + MURNAU_STIFTUNG_MAX_DETAIL_PAGES,
        )
        self.assertTrue(
            all(row["platform"] == "Murnau-Stiftung Filmsuche" for row in links)
        )

    def test_physical_holdings_floor_does_not_define_public_catalog_completeness(self):
        def robots_checker(_url):
            return True, "robots_evaluated"

        def fetch(url):
            if url.endswith("/filmbestand"):
                return FakeResponse(HOLDINGS_HTML, url)
            if "/list/movies/letter/" in url:
                letter = url.rstrip("/").rsplit("/", 1)[-1].upper()
                return FakeResponse(
                    synthetic_letter_page(letter, count=1),
                    url,
                )
            if "/movie/" in url:
                return FakeResponse(DETAIL_HTML, url)
            raise AssertionError(url)

        _, summary, links, _ = collect_murnau_stiftung_dataset(
            fetch=fetch,
            robots_checker=robots_checker,
        )
        self.assertEqual(len(links), 26)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertFalse(summary[0]["priority_review"])
        self.assertIn("não denominador de completude", summary[0]["warning"])

    def test_failed_alpha_partition_marks_snapshot_unstable(self):
        def robots_checker(_url):
            return True, "robots_evaluated"

        def fetch(url):
            if url.endswith("/filmbestand"):
                return FakeResponse(HOLDINGS_HTML, url)
            if url.endswith("/letter/Q"):
                raise RuntimeError("synthetic partition failure")
            if "/list/movies/letter/" in url:
                letter = url.rstrip("/").rsplit("/", 1)[-1].upper()
                return FakeResponse(synthetic_letter_page(letter, count=2), url)
            if "/movie/" in url:
                return FakeResponse(DETAIL_HTML, url)
            raise AssertionError(url)

        _, summary, _, internal = collect_murnau_stiftung_dataset(
            fetch=fetch,
            robots_checker=robots_checker,
        )
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertTrue(summary[0]["priority_review"])
        self.assertTrue(
            any(
                row["status"] == "erro" and row["internal_page"].endswith("/letter/Q")
                for row in internal
            )
        )

    def test_promoted_murnau_remains_active_after_queue_advances_past_gosfilmofond(self):
        corpus = CORPORA["murnau-stiftung"]
        self.assertTrue(corpus["organism_active"])
        self.assertTrue(corpus["monthly_refresh_enabled"])
        self.assertEqual(corpus["code"], "murnau_stiftung")
        self.assertIn("3.889", corpus["audiovisual_scope_note"])

        registry = build_europe_research_registry()
        murnau = registry.loc[
            registry["unit_code"] == "murnau_stiftung"
        ].iloc[0]
        self.assertEqual(murnau["organism_status"], "ativo")
        self.assertEqual(murnau["queue_layer"], "corpus_ativo")

        queue = build_europe_research_queue(registry)
        self.assertNotIn(
            "efg-friedrich-wilhelm-murnau-stiftung",
            set(registry["unit_code"].astype(str)),
        )
        self.assertNotIn(
            "murnau_stiftung",
            set(queue["unit_code"].astype(str)),
        )
        candidates = select_inclusion_candidates(
            queue.to_dict(orient="records"),
            limit=1,
        )
        # Jean Vigo (#80) was analyzed and protocolled in HOLD, so it must
        # remain counted without occupying the next inclusion-candidate slot.
        jean_vigo = registry.loc[
            registry["unit_code"] == "inedits-jean-vigo-institute"
        ].iloc[0]
        self.assertEqual(jean_vigo["organism_status"], "protocolado")
        self.assertNotIn(
            "inedits-jean-vigo-institute",
            set(queue["unit_code"].astype(str)),
        )
        self.assertEqual(candidates[0].unit_code, "fiaf-kavi")
        self.assertEqual(candidates[0].rank, 82)

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
