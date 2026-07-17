import unittest
from unittest.mock import Mock, patch

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link
from memoria_audiovisual.dff import (
    DFF_INSTITUTION_NAME,
    collect_dff_dataset,
    collect_dff_institutions,
    parse_dff_video_catalog_page,
    parse_dff_video_detail_page,
)


class DFFCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_german_film_institute(self):
        institutions = collect_dff_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], DFF_INSTITUTION_NAME)
        self.assertEqual(institutions[0]["country"], "Germany")
        self.assertEqual(institutions[0]["continent"], "Europe")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_catalog_page_deduplicates_public_video_links(self):
        html = """
        <html><body>
            <p>Insgesamt: 6.771 Videos</p>
            <a href="/video/death-mills-1945"></a>
            <a href="/video/death-mills-1945">Death mills (1945) - Filmanfang</a>
            <a href="/video/hans-juergen-syberberg-zu-gast-im-dff">Hans-Jürgen Syberberg zu Gast im DFF</a>
        </body></html>
        """

        parsed = parse_dff_video_catalog_page(html)

        self.assertEqual(parsed["declared_total"], 6771)
        self.assertEqual(len(parsed["records"]), 2)
        self.assertEqual(parsed["records"][0]["title"], "Death mills (1945) - Filmanfang")

    def test_parse_detail_page_detects_metadata_and_embedded_player(self):
        html = """
        <html><body>
            <h1>Death mills (1945) - Filmanfang</h1>
            <div class="video-submitted-on">Eingestellt am: 27.08.2024 | Länge: 06:36 min</div>
            <iframe data-src="https://player.vimeo.com/video/998191164"></iframe>
            <div class="field field--label-inline"><div class="field__label">Regie</div><div class="field__item">Hanuš Burger</div></div>
            <div class="field field--label-inline"><div class="field__label">Quelle</div><div class="field__item">DFF - Deutsches Filminstitut & Filmmuseum</div></div>
            <div class="field--label-inline"><div class="field__label">Kategorie</div><span class="field__items"><span>Filmanfänge</span></span></div>
            <div class="field--label-inline"><div class="field__label">Thema</div><span class="field__items"><span>Förderprogramm Filmerbe (FFE)</span></span></div>
            <div class="field--name-field-edm-video-body-de">Filminhalt: Dokumentarfilm über das Grauen des Nationalsozialismus.</div>
        </body></html>
        """

        record = parse_dff_video_detail_page(html, "https://www.filmportal.de/video/death-mills-1945")

        self.assertEqual(record["title"], "Death mills (1945) - Filmanfang")
        self.assertEqual(record["date"], "2024-08-27")
        self.assertTrue(record["embedded"])
        self.assertIn("Filmanfänge", record["subject"])
        self.assertIn("player incorporado", record["description"])

    def test_collect_dataset_with_mocked_fetch_materializes_video(self):
        catalog_html = """
        <html><body>
            <p>Insgesamt: 6.771 Videos</p>
            <a href="/video/death-mills-1945">Death mills (1945) - Filmanfang</a>
        </body></html>
        """
        detail_html = """
        <html><body>
            <h1>Death mills (1945) - Filmanfang</h1>
            <div class="video-submitted-on">Eingestellt am: 27.08.2024 | Länge: 06:36 min</div>
            <iframe data-src="https://player.vimeo.com/video/998191164"></iframe>
            <div class="field field--label-inline"><div class="field__label">Quelle</div><div class="field__item">DFF - Deutsches Filminstitut & Filmmuseum</div></div>
            <div class="field--label-inline"><div class="field__label">Kategorie</div><span class="field__items"><span>Filmanfänge</span></span></div>
            <div class="field--name-field-edm-video-body-de">Filminhalt: Dokumentarfilm histórico.</div>
        </body></html>
        """

        def fake_fetch(url):
            if "/video/death-mills-1945" in url:
                return Mock(status_code=200, url=url, text=detail_html)
            if "filmportal.de/videos" in url:
                return Mock(status_code=200, url=url, text=catalog_html)
            return Mock(status_code=200, url=url, text="<html></html>")

        with patch("memoria_audiovisual.dff._fetch", side_effect=fake_fetch):
            institutions, summary, video_links, internal_pages = collect_dff_dataset()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(len(video_links), 1)
        self.assertEqual(summary[0]["integrity_status"], "integro")
        self.assertEqual(summary[0]["video_links_found_total"], 1)
        self.assertTrue(any(page["embedded_signals"] == 1 for page in internal_pages))

    def test_platform_theme_and_access_are_classified(self):
        url = "https://www.filmportal.de/video/death-mills-1945"
        row = {
            "platform": "filmportal.de",
            "video_link": url,
            "video_title": "Death mills (1945) - Filmanfang",
            "video_subject": "Filmanfänge; Förderprogramm Filmerbe",
            "video_description": "Dokumentarfilm histórico em ficha pública do DFF.",
        }

        self.assertEqual(classify_platform(url), "filmportal.de")
        self.assertTrue(is_probably_video_link(url, "filmportal.de"))
        self.assertEqual(classify_access_surface(row), "Arquivo cinematográfico público em filmportal.de")
        self.assertEqual(infer_video_theme(row), "Trecho de filme e patrimônio cinematográfico")


if __name__ == "__main__":
    unittest.main()
