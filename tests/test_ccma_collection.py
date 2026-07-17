import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.ccma import (
    build_ccma_search_url,
    collect_ccma_institutions,
    parse_ccma_search_payload,
    parse_ccma_video_item,
)


SEARCH_PAYLOAD = {
    "resposta": {
        "status": "OK",
        "items": {
            "num": 2,
            "item": [
                {"id": 4303570, "tipologia": "DTY_VIDEO_MM", "titol": "Galeria Oberta"},
                {"id": 1194395, "tipologia": "DTY_AUDIO_MM", "titol": "Àudio fora do escopo"},
            ],
        },
        "paginacio": {"total_items": 1},
    }
}


VIDEO_ITEM = {
    "embedable": True,
    "entradeta": "Tots els programes de Galeria Oberta estan ja digitalitzats.",
    "avantitol": "Descobreix l'arxiu de TV3",
    "tipus_contingut": "ALTRES",
    "durada": "00:44:50:23",
    "tipologia": "DTY_VIDEO_MM",
    "nom_friendly": "galeria-oberta",
    "permatitle": "Galeria Oberta",
    "programa": "Descobreix l'arxiu de TV3",
    "bbands": [{"desc": "Descobreix l'arxiu de TVC"}],
    "idiomes": [{"desc": "Català"}],
    "geolocalitzacions": [{"desc": "No geolocalitzat"}],
    "id": 4303570,
    "titol": "Galeria Oberta",
    "data_publicacio": "24/10/2012 22:55:08",
    "data_emissio": "15/03/1985 00:00:00",
    "imatges": [{"text": "https://img.3cat.cat/multimedia/jpg/4/7/1351112237574.jpg"}],
}


class CcmaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_ccma_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertIn("CCMA", institutions[0]["institution"])
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_build_search_url_uses_public_search_api(self):
        url = build_ccma_search_url(2)

        self.assertIn("https://api.3cat.cat/cercador/tot?", url)
        self.assertIn("pagina=2", url)
        self.assertIn("tipologia=DTY_VIDEO_MM", url)

    def test_parse_search_payload_keeps_only_video_records(self):
        records = parse_ccma_search_payload(SEARCH_PAYLOAD)

        self.assertEqual([record["record_id"] for record in records], ["4303570"])

    def test_parse_video_item_extracts_public_player_and_metadata(self):
        row = parse_ccma_video_item(VIDEO_ITEM)

        self.assertEqual(row["record_id"], "4303570")
        self.assertEqual(row["platform"], "3Cat")
        self.assertIn("/4303570/embed/", row["video_link"])
        self.assertIn("Descobreix l'arxiu de TV3", row["subject"])
        self.assertEqual(infer_video_theme(row), "Memória televisiva e arquivo público")
        self.assertEqual(classify_access_surface(row), "Arquivo televisivo público em plataforma 3Cat")


if __name__ == "__main__":
    unittest.main()
