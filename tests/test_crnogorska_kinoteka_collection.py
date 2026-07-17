import unittest
from unittest.mock import Mock, patch

from memoria_audiovisual.crnogorska_kinoteka import (
    CRNOGORSKA_KINOTEKA_INSTITUTION_NAME,
    collect_crnogorska_kinoteka_dataset,
    collect_crnogorska_kinoteka_institutions,
    parse_crnogorska_kinoteka_detail_page,
)


class CrnogorskaKinotekaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_montenegrin_film_archive(self):
        institutions = collect_crnogorska_kinoteka_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], CRNOGORSKA_KINOTEKA_INSTITUTION_NAME)
        self.assertEqual(institutions[0]["country"], "Montenegro")
        self.assertEqual(institutions[0]["continent"], "Europe")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_detail_page_detects_efg_player_shell(self):
        html = """
        <html><body>
            <h1>Non è resurrezione senza morte</h1>
            <video class="video-js" data-setup='{"sources": []}'></video>
            <a href="http://kinoteka.me/arhiv/voskrsenje-film.html">View at CK</a>
        </body></html>
        """

        record = parse_crnogorska_kinoteka_detail_page(html)

        self.assertEqual(record["title"], "Non è resurrezione senza morte")
        self.assertTrue(record["has_player_shell"])
        self.assertIn("Primeira Guerra Mundial", record["description"])
        self.assertEqual(record["external_view_url"], "http://kinoteka.me/arhiv/voskrsenje-film.html")

    def test_collect_dataset_keeps_known_record_when_detail_route_fails(self):
        def fake_fetch(url):
            if "detail" in url:
                raise RuntimeError("rota EFG instável")
            return Mock(status_code=200, url=url, text="<html></html>")

        with patch("memoria_audiovisual.crnogorska_kinoteka._fetch", side_effect=fake_fetch):
            institutions, summary, video_links, internal_pages = collect_crnogorska_kinoteka_dataset()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(len(video_links), 1)
        self.assertEqual(summary[0]["integrity_status"], "instavel")
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertTrue(any(page["status"] == "erro" for page in internal_pages))


if __name__ == "__main__":
    unittest.main()
