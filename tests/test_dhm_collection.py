import unittest

from memoria_audiovisual.dhm import (
    collect_dhm_institutions,
    parse_dhm_detail_page,
    parse_dhm_marshall_plan_page,
)


class DHMCollectionTests(unittest.TestCase):
    def test_collect_dhm_institutions_declares_single_archive(self):
        institutions = collect_dhm_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["country"], "Germany")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_marshall_plan_page_collects_linked_and_unlinked_films(self):
        html = """
        <main>
          <article class="grid-teaser__content-wrapper">
            <div class="grid-teaser__content">
              <a href="/zeughauskino/en/programs/zeughauskino-online/films-of-the-marshall-plan/air-of-freedom/">
                <picture><source type="image/png" data-srcset="/image.png"></picture>
              </a>
              <div class="grid-teaser__infobox">
                <header><h3><a href="/zeughauskino/en/programs/zeughauskino-online/films-of-the-marshall-plan/air-of-freedom/">Air of Freedom</a></h3></header>
                <p>BRD 1951, P: ECA Western Germany</p>
              </div>
            </div>
          </article>
          <article class="grid-teaser__content-wrapper">
            <div class="grid-teaser__infobox">
              <header><h3><span>Clearing The Lines</span></h3></header>
              <p>GB 1951, R: Kay Mander</p>
            </div>
          </article>
        </main>
        """

        records = parse_dhm_marshall_plan_page(html)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["title"], "Air of Freedom")
        self.assertTrue(records[0]["detail_available"])
        self.assertEqual(records[1]["title"], "Clearing The Lines")
        self.assertFalse(records[1]["detail_available"])
        self.assertIn("#clearing-the-lines", records[1]["page_url"])

    def test_parse_detail_page_extracts_metadata_without_player_assumption(self):
        html = """
        <main>
          <h1>Air of Freedom</h1>
          Produced by:
          ECA Western Germany
          Country/Year:
          BRD 1951
          Length :
          11'
          Language :
          English
          Format:
          16mm, mono, b/w
          Famed radio station RIAS is featured in this report.
        </main>
        """

        record = parse_dhm_detail_page(
            html,
            "https://www.dhm.de/zeughauskino/en/filmreihen/online-filmreihen/filme-des-marshall-plans/air-of-freedom/",
        )

        self.assertEqual(record["title"], "Air of Freedom")
        self.assertEqual(record["date"], "1951")
        self.assertIn("ECA Western Germany", record["subject"])
        self.assertIn("RIAS", record["description"])
        self.assertFalse(record["embedded"])


if __name__ == "__main__":
    unittest.main()
