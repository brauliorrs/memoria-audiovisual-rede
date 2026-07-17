import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cdna import collect_cdna_institutions, parse_cdna_api_payload


class CdnaCollectionTests(unittest.TestCase):
    def test_collect_cdna_institutions_declares_single_archive(self):
        institutions = collect_cdna_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque de Nouvelle-Aquitaine")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_cdna_api_payload_extracts_public_video_records(self):
        payload = {
            "count": {"nbr": 4724},
            "data": [
                {
                    "id": 8281,
                    "sid": 1,
                    "oid": 8281,
                    "titre": "Afghanistan 75",
                    "resume": "Documentaire tourné en Afghanistan.",
                    "descriptif": "Portraits, pratiques culturelles et scènes de marché.",
                    "annee": "1975",
                    "duree": "0:22:00",
                    "date_publication": "2026-06-08",
                    "internet_permalien": "c-p16-das01-0010-do",
                    "slug": "films/c-p16-das01-0010-do",
                    "enveloppe": "20260608161107491",
                    "film": "Afghanistan 75_WEB.mp4",
                    "realisateurs_decoded": [{"type": 2, "prenom": "Alain", "nom": "DASSÉ"}],
                }
            ],
        }

        records, declared_total = parse_cdna_api_payload(payload)

        self.assertEqual(declared_total, 4724)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "8281")
        self.assertEqual(records[0]["title"], "Afghanistan 75")
        self.assertEqual(records[0]["date"], "1975")
        self.assertIn("Alain DASSÉ", records[0]["subject"])
        self.assertIn("Afghanistan%2075_WEB.mp4", records[0]["video_link"])
        self.assertTrue(records[0]["embedded"])

    def test_cdna_theme_and_access_are_specific(self):
        row = {
            "platform": "Cinémathèque de Nouvelle-Aquitaine",
            "video_link": "https://videos-cdna.memoirefilmiquenouvelleaquitaine.fr/20260608161107491/Afghanistan%2075_WEB.mp4",
            "video_title": "Afghanistan 75",
            "video_subject": "Alain DASSÉ",
            "video_description": "Scènes de marché, portraits et pratiques culturelles.",
        }

        self.assertEqual(infer_video_theme(row), "Documentário, cotidiano e memória local")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
