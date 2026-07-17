import unittest

from memoria_audiovisual.fina import build_fina_video_list_url, parse_fina_record


class FinaCollectionTests(unittest.TestCase):
    def test_build_video_list_url_uses_public_video_category(self):
        url = build_fina_video_list_url(first_result=500, max_results=500)

        self.assertIn("platform=BROWSER", url)
        self.assertIn("firstResult=500", url)
        self.assertIn("mainCategoryId[]=1", url)

    def test_parse_record_keeps_video_metadata_and_access_flags(self):
        item = {
            "id": 53713,
            "title": "Najmniejszy pies na świecie | Kronika PAT 1937",
            "lead": "Odcinek Tygodnika PAT",
            "webUrl": "https://ninateka.pl/movies,1/najmniejszy-pies,53713",
            "mainCategory": {"id": 1, "name": "video", "slug": "movies"},
            "categories": [{"name": "KRÓTKOMETRAŻOWE"}],
            "tags": [{"name": "polska agencja telegraficzna"}],
            "duration": 41,
            "payable": False,
            "loginRequired": False,
            "video": True,
            "platforms": [{"name": "BROWSER"}],
        }
        detail = {
            "description": "<p>Pies, który mieści się w kieszonce.</p>",
            "countries": [{"name": "Polska"}],
            "persons": {"PRODUCTION": [{"name": "Polska Agencja Telegraficzna"}]},
        }

        record = parse_fina_record(item, detail)

        self.assertEqual(record["record_id"], "53713")
        self.assertEqual(record["platform"], "Ninateka")
        self.assertEqual(record["main_category_id"], 1)
        self.assertFalse(record["payable"])
        self.assertFalse(record["login_required"])
        self.assertTrue(record["browser_platform"])
        self.assertIn("KRÓTKOMETRAŻOWE", record["subject"])
        self.assertIn("Pies, który mieści się w kieszonce", record["description"])


if __name__ == "__main__":
    unittest.main()
