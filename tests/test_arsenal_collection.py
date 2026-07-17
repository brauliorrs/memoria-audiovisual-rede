import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.arsenal import collect_arsenal_institutions, parse_arsenal_browse_page
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


ARSENAL_BROWSE_HTML = """
<html><body>
  <h1>7182 Werke gefunden</h1>
  <div class="bResultItemText">
    <a href="/Detail/works/6750">"Le-deu-pil-teo-ga Cheol-hoe-doeb-ni-da."</a>
    <div>("The red filter is withdrawn.")</div>
    <div>Minjung Kim, Republik Korea, 2020, Englisch, Koreanisch</div>
  </div>
  <div class="bResultItemText">
    <a href="/Detail/works/3997">&lt;IO&gt;</a>
    <div>Steffen Ramlow, Deutschland, 2001, Kein Dialog</div>
  </div>
  <div class="jscroll-next-parent">
    <a href="/Browse/Works/s/36/key/abc123/view/images/sort/Titel/_advanced/0" class="jscroll-next">Vor 36</a>
  </div>
</body></html>
"""


class ArsenalCollectionTests(unittest.TestCase):
    def test_collect_arsenal_institutions_declares_single_archive(self):
        institutions = collect_arsenal_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "DE-ARSENAL")
        self.assertEqual(institutions[0]["country"], "Germany")

    def test_parse_arsenal_browse_page_extracts_records_and_pagination(self):
        page_data = parse_arsenal_browse_page(ARSENAL_BROWSE_HTML)

        self.assertEqual(page_data["total"], 7182)
        self.assertEqual(page_data["result_key"], "abc123")
        self.assertEqual(len(page_data["records"]), 2)
        self.assertEqual(page_data["records"][0]["record_id"], "6750")
        self.assertEqual(page_data["records"][0]["date"], "2020")
        self.assertIn("Republik Korea", page_data["records"][0]["subject"])

    def test_arsenal_urls_are_classified_as_institutional_catalog_records(self):
        url = "https://films.arsenal-berlin.de/Detail/works/6750"

        self.assertEqual(classify_platform(url), "Arsenal Film Database")
        self.assertTrue(is_probably_video_link(url, "Arsenal Film Database"))
        self.assertEqual(
            classify_access_surface({"platform": "Arsenal Film Database", "video_link": url}),
            "Catálogo descritivo audiovisual institucional",
        )

    def test_arsenal_theme_is_catalog_metadata(self):
        theme = infer_video_theme(
            {
                "platform": "Arsenal Film Database",
                "video_title": "<IO>",
                "video_subject": "Steffen Ramlow, Deutschland, 2001, Kein Dialog",
                "video_description": "Registro do índice público Browse Works.",
            }
        )

        self.assertEqual(theme, "Catálogo filmográfico e metadados de acervo")


if __name__ == "__main__":
    unittest.main()
