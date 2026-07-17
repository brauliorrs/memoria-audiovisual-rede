import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.autrefois import (
    collect_autrefois_institutions,
    parse_autrefois_video_post,
)


class AutrefoisCollectionTests(unittest.TestCase):
    def test_collect_autrefois_institutions_declares_single_archive(self):
        institutions = collect_autrefois_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "CH-AUTREFOIS-GENEVE")
        self.assertEqual(institutions[0]["country"], "Switzerland")

    def test_parse_autrefois_video_post_extracts_video_source_and_terms(self):
        post = {
            "id": 8226,
            "date": "2022-04-05T14:05:39",
            "slug": "metiers-du-traitement-de-leau",
            "link": "https://www.autrefoisgeneve.ch/aiovg_videos/metiers-du-traitement-de-leau/",
            "title": {"rendered": "Métiers du traitement de l’eau"},
            "content": {"rendered": "<p>Histoire de l’assainissement à Genève.</p>"},
            "excerpt": {"rendered": ""},
            "aiovg_tags": [88],
        }
        html = """
        <main>
          <h1>Métiers du traitement de l’eau</h1>
          <video controls><source src="https://play.vod2.infomaniak.com/single/abc/def/ghi"/></video>
        </main>
        """

        record = parse_autrefois_video_post(post, html, {88: "Entre2prises"})

        self.assertEqual(record["record_id"], "8226")
        self.assertEqual(record["video_link"], "https://play.vod2.infomaniak.com/single/abc/def/ghi")
        self.assertEqual(record["platform"], "Autrefois Genève")
        self.assertIn("Entre2prises", record["description"])
        self.assertIn("assainissement", record["description"])
        self.assertTrue(record["embedded"])
        self.assertEqual(record["date"], "2022-04-05")

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Infraestrutura urbana e serviços públicos")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
