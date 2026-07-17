import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.iam import collect_iam_institutions, parse_iam_media_post


class IamCollectionTests(unittest.TestCase):
    def test_collect_iam_institutions_declares_single_archive(self):
        institutions = collect_iam_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "MC-IAM")
        self.assertEqual(institutions[0]["country"], "Monaco")

    def test_parse_iam_media_post_extracts_video_source_and_terms(self):
        post = {
            "id": 6140,
            "date": "2026-06-01T09:19:59",
            "slug": "ambiances-de-grand-prix",
            "link": "https://institut-audiovisuel.mc/medias/ambiances-de-grand-prix/",
            "title": {"rendered": "Ambiances de Grand Prix"},
            "class_list": [
                "fonds-fonds-biancheri",
                "lieux-monaco",
                "mots-cles-grand-prix",
                "periode-annees-1970s",
                "supports-8-mm",
                "types-de-documents-film-amateur",
                "specificites-techniques-couleur",
            ],
        }
        html = """
        <main>
          <h1>Ambiances de Grand Prix</h1>
          <video controls><source src="https://example.org/video.mov" type="video/mp4"/></video>
          <p>Images de course automobile à Monaco en 1974.</p>
        </main>
        """

        record = parse_iam_media_post(post, html)

        self.assertEqual(record["record_id"], "6140")
        self.assertEqual(record["video_link"], "https://example.org/video.mov")
        self.assertEqual(record["platform"], "Institut audiovisuel de Monaco")
        self.assertIn("grand prix", record["description"])
        self.assertIn("film amateur", record["description"])
        self.assertTrue(record["embedded"])
        self.assertEqual(record["date"], "1974")

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Esporte e automobilismo")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
