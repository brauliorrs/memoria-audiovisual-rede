import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.bnt import (
    collect_bnt_institutions,
    parse_bnt_detail_html,
)


class BntCollectionTests(unittest.TestCase):
    def test_collect_bnt_institutions_declares_single_archive(self):
        institutions = collect_bnt_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "BG-BNT")
        self.assertEqual(institutions[0]["country"], "Bulgaria")

    def test_parse_bnt_detail_html_extracts_public_video_metadata(self):
        html = """
        <html>
          <body>
            <h1>Европейски маршрути: Мадрид</h1>
            <video
              id="bnt-video"
              class="video-js"
              data-setup='{"sources":[{"type":"video/mp4","src":"https://p.bnt.bg/e/m/madrid.mp4"}]}'>
            </video>
            <div class="small-txt-wrap">
              <p>Поредицата показва европейски маршрути и културно наследство.</p>
            </div>
            <span>17:05, 15.11.2019</span>
          </body>
        </html>
        """

        record = parse_bnt_detail_html(
            "https://bnt.bg/bg/a/evropejski-marshruti-madrid",
            html,
            listing_title="Европейски маршрути: Мадрид",
            listing_text="Европейски маршрути: Мадрид 17:05, 15.11.2019",
            page_number=3,
        )

        self.assertEqual(record["record_id"], "evropejski-marshruti-madrid")
        self.assertEqual(record["platform"], "BNT.bg")
        self.assertEqual(record["date"], "2019-11-15")
        self.assertTrue(record["embedded"])
        self.assertIn("https://p.bnt.bg/e/m/madrid.mp4", record["description"])

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "História, memória e patrimônio")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo televisivo público em site institucional")


if __name__ == "__main__":
    unittest.main()
