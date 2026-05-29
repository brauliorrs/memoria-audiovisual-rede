import unittest
from unittest.mock import patch

from memoria_audiovisual.aamod import (
    collect_aamod_institutions,
    parse_aamod_film_page,
    parse_aamod_film_post,
    parse_aamod_home_page,
)
from memoria_audiovisual.analysis import classify_access_surface
from memoria_audiovisual.crawler import classify_platform, is_probably_video_link


class AamodCollectionTests(unittest.TestCase):
    def test_collect_aamod_institutions_declares_single_archive(self):
        institutions = collect_aamod_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "IT-AAMOD")
        self.assertEqual(institutions[0]["country"], "Italy")

    def test_parse_aamod_home_page_extracts_youtube_embeds(self):
        html = """
        <html><body>
            <iframe src="https://www.youtube.com/embed/abc123?start=20&feature=oembed"></iframe>
            <iframe src="https://www.youtube.com/embed/abc123?feature=oembed"></iframe>
        </body></html>
        """

        with patch("memoria_audiovisual.aamod._youtube_oembed", return_value={"title": "AAMOD video"}):
            records = parse_aamod_home_page(html)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["title"], "AAMOD video")
        self.assertEqual(records[0]["platform"], "YouTube")
        self.assertTrue(records[0]["embedded"])

    def test_parse_aamod_film_post_extracts_metadata(self):
        post = {
            "id": 16865,
            "link": "https://aamod.it/i-nostri-film/sirena-operaia/",
            "date": "2025-04-24T15:23:01",
            "title": {"rendered": "Sirena operaia"},
            "content": {
                "rendered": (
                    "<p>genere: documentario regia di: Gianfranco Pannone anno: 2000 "
                    "durata: 00:53:29 Il mondo della fabbrica.</p>"
                )
            },
        }

        record = parse_aamod_film_post(post)

        self.assertEqual(record["platform"], "AAMOD")
        self.assertEqual(record["date"], "2000")
        self.assertIn("documentario", record["subject"])
        self.assertIn("sem player", record["description"])

    def test_parse_aamod_film_page_extracts_public_page_metadata(self):
        html = """
        <main>
            <h1>Sirena operaia</h1>
            Sirena operaia genere: documentario regia di: Gianfranco Pannone
            anno: 2000 durata: 00:53:29 Il mondo della fabbrica.
        </main>
        """

        record = parse_aamod_film_page(html, "https://aamod.it/i-nostri-film/sirena-operaia/")

        self.assertEqual(record["date"], "2000")
        self.assertEqual(record["subject"], "documentario")
        self.assertIn("Gianfranco Pannone", record["description"])

    def test_aamod_urls_are_classified_as_video_surface(self):
        url = "https://aamod.it/i-nostri-film/sirena-operaia/"

        self.assertEqual(classify_platform(url), "AAMOD")
        self.assertTrue(is_probably_video_link(url, "AAMOD"))
        self.assertEqual(
            classify_access_surface({"platform": "AAMOD", "video_link": url}),
            "Arquivo audiovisual institucional",
        )


if __name__ == "__main__":
    unittest.main()
