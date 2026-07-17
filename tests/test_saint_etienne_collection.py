import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.saint_etienne import (
    collect_saint_etienne_institutions,
    extract_saint_etienne_detail_links,
    parse_saint_etienne_detail_page,
)


class SaintEtienneCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_saint_etienne_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque de Saint-Étienne")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_extract_detail_links_keeps_oai_links(self):
        html = '<a href="/Default/doc/OAI_1/_b64_abc/adieu-chavanelle?_lg=fr-FR">Adieu</a>'

        links = extract_saint_etienne_detail_links(html, "https://cinematheque.saint-etienne.fr/")

        self.assertEqual(links[0], "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64_abc/adieu-chavanelle?_lg=fr-FR")

    def test_parse_detail_page_extracts_mp4_and_metadata(self):
        html = """
        <html><head><title>Adieu Chavanelle - Cinémathèque de Saint-Etienne</title>
        <meta name="description" content="Évocation nostalgique du marché de gros."></head><body>
        <h1>Adieu Chavanelle</h1>
        SYNOPSIS : Évocation nostalgique des derniers moments du marché.
        FORMAT DE DUREE : CM - Court métrage
        GENRE : Documentaire
        DATE DE REALISATION : 1972
        REALISATEUR : André Picon
        PRODUCTEUR : Films du Hibou
        SON : Sonore
        DUREE : 00:13:30
        IDENTIFIANT : documentaire-5
        FORMAT ORIGINAL : Bétacam
        <a href="https://diazcse.oembed.diazinteregio.org/video/0000-0009/0007-PICON/RT_0005.mp4">mp4</a>
        </body></html>
        """
        record = parse_saint_etienne_detail_page(
            html,
            "https://cinematheque.saint-etienne.fr/Default/doc/OAI_1/_b64/adieu-chavanelle?_lg=fr-FR",
        )

        self.assertEqual(record["record_id"], "documentaire-5")
        self.assertEqual(record["date"], "1972")
        self.assertTrue(record["embedded"])
        self.assertIn("diazcse.oembed", record["video_link"])
        self.assertIn("André Picon", record["subject"])

    def test_saint_etienne_theme_and_access_are_specific(self):
        row = {
            "platform": "Cinémathèque de Saint-Étienne",
            "video_link": "https://diazcse.oembed.diazinteregio.org/video/example.mp4",
            "video_title": "Une capitale industrielle : Saint-Étienne",
            "video_subject": "Documentaire; Office du Cinéma scolaire",
            "video_description": "Film d'archives muet sur Saint-Étienne industrielle.",
        }

        self.assertEqual(infer_video_theme(row), "Território, cidade e memória local")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
