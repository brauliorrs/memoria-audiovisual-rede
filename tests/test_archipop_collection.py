import unittest

from memoria_audiovisual.archipop import (
    collect_archipop_institutions,
    parse_archipop_film_page,
    parse_archipop_list_page,
)
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


class ArchipopCollectionTests(unittest.TestCase):
    def test_collect_archipop_institutions_declares_single_archive(self):
        institutions = collect_archipop_institutions()
        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "ARCHIPOP")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_archipop_list_page_detects_film_links(self):
        html = """
        <a href="/les-films-dunes-570-1297-1-0.html">Dunes</a>
        <a href="/contact">Contact</a>
        <a href="/les-films-dunes-570-1297-1-0.html">En savoir +</a>
        """
        records = parse_archipop_list_page(html, "https://lesfilms.archipop.org/")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "Dunes")
        self.assertIn("les-films-dunes", records[0]["film_url"])

    def test_parse_archipop_film_page_extracts_metadata_and_embed(self):
        html = """
        <h1>Les films</h1><h1>Dunes</h1>
        <iframe src="https://diazarchipop.oembed.diazinteregio.org/embed/0130_0139/0138FS0036?feature=oembed"></iframe>
        <ul>
          <li class="val">Cinéaste(s) : Michel JEANSON</li>
          <li class="val">Année(s) : 1954</li>
          <li class="val">Durée : 00:16:55</li>
          <li class="val">Format : Film 16 mm</li>
          <li class="val">Son : Muet</li>
          <li class="val">Genre : Documentaire</li>
          <li class="val">Collection : Paul JEANSON</li>
          <li class="val">Support(s) : 0138FS0036</li>
        </ul>
        <div class="Resume">Le massif dunaire du Marquenterre en 1954.</div>
        <div class="diaKeywords">Dune Sable Tracteur agricole</div>
        """
        record = parse_archipop_film_page(
            html,
            "https://lesfilms.archipop.org/les-films-dunes-570-1297-1-0.html",
        )
        self.assertEqual(record["record_id"], "1297")
        self.assertEqual(record["title"], "Dunes")
        self.assertEqual(record["year"], "1954")
        self.assertEqual(record["duration"], "00:16:55")
        self.assertEqual(record["creator"], "Michel JEANSON")
        self.assertTrue(record["has_public_player"])
        self.assertIn("Dune", record["keywords"])

    def test_archipop_urls_are_classified_as_video_surface(self):
        film_url = "https://lesfilms.archipop.org/les-films-dunes-570-1297-1-0.html"
        embed_url = "https://diazarchipop.oembed.diazinteregio.org/embed/0130_0139/0138FS0036?feature=oembed"
        self.assertEqual(classify_platform(film_url), "Archipop")
        self.assertTrue(is_probably_video_link(film_url, "Archipop"))
        self.assertTrue(is_probably_video_link(embed_url, "Archipop"))


if __name__ == "__main__":
    unittest.main()
