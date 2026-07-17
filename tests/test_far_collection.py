import unittest

from memoria_audiovisual.far import (
    build_far_search_payload,
    build_far_video_url,
    is_audio_only_far_record,
    parse_far_record,
)


class FarCollectionTests(unittest.TestCase):
    def test_build_search_payload_targets_far_library(self):
        payload = build_far_search_payload(page=2, results_per_page=50)

        self.assertEqual(payload["currentPage"], 2)
        self.assertEqual(payload["resultsPerPage"], 50)
        self.assertEqual(payload["filters"]["general"]["sid"], 2)

    def test_parse_record_keeps_video_metadata(self):
        labels = {
            "genre": {"195": "Documentaire"},
            "theme": {"210": "Société", "199": "Architecture, habitat"},
            "format": {"200": "Numérique"},
        }
        record = {
            "id": 9163,
            "sid": 2,
            "oid": 869,
            "slug": "films/le-creav-et-tele-mirabeau",
            "titre": "Le CREAV et Télé Mirabeau",
            "resume": "<p>Compilation de films d'archives.</p>",
            "annee": "2023",
            "duree": "0:34:08",
            "genre": 195,
            "theme": 210,
            "themes_secondaires": "199",
            "format_original": 200,
            "video_url": "https://videos.far-asso.fr/20231109164646577/master.mp4",
            "realisateurs_decoded": [{"prenom": "Maxim", "nom": "PRÉVÔT"}],
        }

        parsed = parse_far_record(record, labels)

        self.assertEqual(parsed["record_id"], "9163")
        self.assertEqual(parsed["platform"], "MFNA / FAR")
        self.assertEqual(parsed["video_link"], record["video_url"])
        self.assertFalse(parsed["audio_only"])
        self.assertIn("Documentaire", parsed["subject"])
        self.assertIn("Société", parsed["subject"])
        self.assertIn("Maxim PRÉVÔT", parsed["subject"])

    def test_audio_only_filter_rejects_radio_and_sound_records(self):
        labels = {
            "genre": {"199": "Journal radio"},
            "theme": {"239": "Archives sonores"},
            "format": {"212": "Bande son"},
        }

        self.assertTrue(is_audio_only_far_record({"genre": 199}, labels))
        self.assertTrue(is_audio_only_far_record({"theme": 239}, labels))
        self.assertTrue(is_audio_only_far_record({"format_original": 212}, labels))

    def test_build_video_url_uses_public_video_domain(self):
        url = build_far_video_url({"enveloppe": "20231109164646577", "film": "master file.mp4"})

        self.assertEqual(url, "https://videos.far-asso.fr/20231109164646577/master%20file.mp4")


if __name__ == "__main__":
    unittest.main()
