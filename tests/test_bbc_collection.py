import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.bbc import (
    collect_bbc_institutions,
    parse_bbc_video_promo,
)


class BbcCollectionTests(unittest.TestCase):
    def test_collect_bbc_institutions_declares_single_archive(self):
        institutions = collect_bbc_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "GB-BBC-ARCHIVE")
        self.assertEqual(institutions[0]["country"], "United Kingdom")

    def test_parse_bbc_video_promo_extracts_public_video_metadata(self):
        promo = {
            "urn": "urn:bbc:optimo:asset:c2l3lgngky0o",
            "url": "/videos/c2l3lgngky0o",
            "headline": "1986: Tidy Up Walsall",
            "description": "Comedy campaign to Tidy Up Walsall.",
            "duration": 393000,
            "lastPublished": "1986-06-13T00:00:00.000Z",
            "type": "video",
            "pageTypeIndicator": {"altText": "Video, 00:06:33", "text": "6:33"},
            "metadataStripItems": [
                {"label": "Posted", "text": "18 Jun 2024"},
                {"label": "Attribution", "text": "BBC"},
            ],
            "image": {"alt": "Bill Tidy in Walsall"},
        }

        record = parse_bbc_video_promo(promo, "Gems from the Archive", 1)

        self.assertEqual(record["record_id"], "c2l3lgngky0o")
        self.assertEqual(record["video_link"], "https://www.bbc.co.uk/videos/c2l3lgngky0o")
        self.assertEqual(record["platform"], "BBC Archive")
        self.assertIn("Gems from the Archive", record["description"])
        self.assertIn("06:33", record["description"])
        self.assertTrue(record["embedded"])
        self.assertEqual(record["date"], "1986")

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Artes, cultura e entretenimento")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo televisivo público curado")


if __name__ == "__main__":
    unittest.main()
