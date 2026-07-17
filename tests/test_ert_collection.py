import unittest

from memoria_audiovisual.ert import collect_ert_institutions, parse_ert_post


class ERTCollectionTests(unittest.TestCase):
    def test_collect_ert_institutions_declares_single_archive(self):
        institutions = collect_ert_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "GR-ERT")
        self.assertEqual(institutions[0]["country"], "Greece")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_ert_post_extracts_video_metadata(self):
        post = {
            "id": 218466,
            "date": "2026-06-29T12:25:49",
            "link": "https://archive.ert.gr/id_206303/",
            "title": {"rendered": "ΤΟ ΜΑΓΙΚΟ ΤΩΝ ΑΝΘΡΩΠΩΝ"},
            "excerpt": {"rendered": "Σύντομη περιγραφή"},
            "content": {
                "rendered": """
                <iframe src="https://archive.ert.gr/assets/archive/webtv/live-uni/vod/player.php?f=0000206303/0001/media206303.mp4"></iframe>
                <p><strong>Κωδικός Τεκμηρίου</strong><br />0000206303</p>
                <p><strong>Τύπος ψηφιακού αρχείου<br /></strong>Βίντεο</p>
                <p><strong>Τίτλος</strong><br />ΤΟ ΜΑΓΙΚΟ ΤΩΝ ΑΝΘΡΩΠΩΝ</p>
                <p><strong>Χρονολογία Παραγωγής<br /></strong>2021</p>
                <p><strong>Κατηγορία</strong><br />ΝΤΟΚΙΜΑΝΤΕΡ ΚΟΙΝΩΝΙΚΟ</p>
                <p><strong>Περίληψη</strong><br />Εκπομπή αφιερωμένη στην προσωπική ιστορία ανθρώπων.</p>
                """
            },
        }

        record = parse_ert_post(post)

        self.assertIsNotNone(record)
        self.assertEqual(record["record_id"], "0000206303")
        self.assertEqual(record["platform"], "ERT Archive")
        self.assertIn("ΝΤΟΚΙΜΑΝΤΕΡ", record["subject"])
        self.assertTrue(record["embedded"])
        self.assertEqual(record["date"], "2021")

    def test_parse_ert_post_rejects_audio_only_metadata(self):
        post = {
            "id": 1,
            "date": "2024-01-01T00:00:00",
            "link": "https://archive.ert.gr/audio/",
            "title": {"rendered": "ΡΑΔΙΟΦΩΝΙΚΟ ΤΕΚΜΗΡΙΟ"},
            "content": {
                "rendered": """
                <p><strong>Κωδικός Τεκμηρίου</strong><br />AUDIO001</p>
                <p><strong>Τύπος ψηφιακού αρχείου<br /></strong>Ήχος</p>
                <p><strong>Τίτλος</strong><br />ΡΑΔΙΟΦΩΝΙΚΟ ΤΕΚΜΗΡΙΟ</p>
                """
            },
        }

        self.assertIsNone(parse_ert_post(post))


if __name__ == "__main__":
    unittest.main()
