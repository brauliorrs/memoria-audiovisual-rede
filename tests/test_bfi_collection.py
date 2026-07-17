import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.bfi import (
    collect_bfi_institutions,
    parse_bfi_replay_record,
)


class BfiCollectionTests(unittest.TestCase):
    def test_collect_bfi_institutions_declares_single_archive(self):
        institutions = collect_bfi_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "GB-BFI-NATIONAL-ARCHIVE")
        self.assertEqual(institutions[0]["country"], "United Kingdom")

    def test_parse_bfi_replay_record_extracts_public_video_metadata(self):
        record = {
            "workUuid": "94be54c1-9c25-503d-badb-f2b607834507",
            "displayTitle": "Emma",
            "genres": ["Drama"],
            "subjects": ["Future", "Cemeteries"],
            "locations": ["Highgate Cemy"],
            "sourceArchive": "",
            "assetId": "ref:Q3M3IzdjryAr1AA4pj4VjSj4vwCMMuH3",
            "accountId": "6057949427001",
            "sound": "Sound",
            "duration": 12,
            "availability": {"locations": ["Internet-UK"]},
        }
        detail_payload = {
            "work": {
                "id": "94be54c1-9c25-503d-badb-f2b607834507",
                "displayTitle": "Emma",
                "dates": {"start": "1965", "type": "Release"},
                "runningTime": 13,
                "synopsis": "A small girl playing in Highgate Cemetery.",
                "genres": ["Drama"],
                "subjects": ["Future", "Cemeteries"],
                "locations": ["Highgate Cemy"],
                "video": {
                    "assetId": "ref:Q3M3IzdjryAr1AA4pj4VjSj4vwCMMuH3",
                    "accountId": "6057949427001",
                    "availability": {"locations": ["Internet-UK"]},
                },
            },
            "video": {
                "assetId": "ref:Q3M3IzdjryAr1AA4pj4VjSj4vwCMMuH3",
                "accountId": "6057949427001",
                "availability": {"locations": ["Internet-UK"]},
            },
        }

        parsed = parse_bfi_replay_record(record, detail_payload, 1)

        self.assertEqual(parsed["record_id"], "94be54c1-9c25-503d-badb-f2b607834507")
        self.assertEqual(
            parsed["video_link"],
            "https://replay.bfi.org.uk/video/94be54c1-9c25-503d-badb-f2b607834507",
        )
        self.assertEqual(parsed["platform"], "BFI Replay")
        self.assertEqual(parsed["date"], "1965")
        self.assertIn("Internet-UK", parsed["description"])
        self.assertTrue(parsed["embedded"])

        analytic_row = {
            "platform": parsed["platform"],
            "video_link": parsed["video_link"],
            "video_title": parsed["title"],
            "video_subject": parsed["subject"],
            "video_description": parsed["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Ficção cinematográfica")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual público curado")


if __name__ == "__main__":
    unittest.main()
