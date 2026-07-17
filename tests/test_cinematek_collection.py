import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinematek import collect_cinematek_institutions, parse_cinematek_home_links


class CinematekCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_cinematek_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque royale de Belgique / CINEMATEK")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_home_links_extracts_external_streaming_routes(self):
        html = """
        <a href="https://www.avilafilm.be/en/film/brussels-transit"></a>
        <a href="https://stream.sooner.be/search/Daens/type/best-match/m/daens"></a>
        <a href="https://cinematek.be/en/collections/film">Film collection</a>
        """
        records = parse_cinematek_home_links(html)

        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["platform"], "CINEMATEK@HOME")
        self.assertIn("Brussels Transit", records[0]["title"])
        self.assertIn("Avila", records[0]["subject"])
        self.assertIn("Sooner", records[1]["subject"])

    def test_cinematek_home_is_restricted_external_access(self):
        row = {
            "platform": "CINEMATEK@HOME",
            "video_link": "https://www.avilafilm.be/en/film/jeanne-dielman-23-quai-du-commerce-1080-bruxelles",
            "video_title": "Jeanne Dielman",
            "video_subject": "CINEMATEK@HOME; Avila",
            "video_description": "Acesso mediado por Avila; sinais de assinatura, aluguel, compra ou login.",
        }

        self.assertEqual(infer_video_theme(row), "Patrimônio cinematográfico e cinefilia")
        self.assertEqual(classify_access_surface(row), "Streaming pago/autenticado em plataforma externa")


if __name__ == "__main__":
    unittest.main()
