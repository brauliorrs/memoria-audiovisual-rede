import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinemateca_portuguesa import (
    collect_cinemateca_portuguesa_institutions,
    parse_cinemateca_portuguesa_detail_page,
    parse_cinemateca_portuguesa_video_list_page,
)


LIST_HTML = """
<div class="CDText w325 fRight">
  <div class="CDTitle"><a href="Ficha.aspx?obraid=13402&type=Video">"A Grande Noite do Comércio"</a></div>
  <p>Portugal, 1947(?)</p>
  <p>Duração: 00:29:08</p>
</div>
<div class="CDText w325 fRight">
  <div class="CDTitle"><a href="Ficha.aspx?obraid=13016&type=Video">"Alter do Chão"</a></div>
  <p>Portugal, 1946(?)</p>
  <p>Duração: 00:29:57</p>
</div>
"""

DETAIL_HTML = """
<html><body>
<div>CINEMATECA DIGITAL</div>
<div>Vídeo</div>
<h1>No Jardim</h1>
<p>Aurélio da Paz dos Reis (1862-1931) - Realizador</p>
<p>Portugal, 1896</p>
<p>Género: documentário</p>
<p>Duração: 00:00:32, 16 fps</p>
<p>Formato: 35 mm, PB, sem som</p>
<p>Descrição: Um dos primeiros filmes portugueses.</p>
<p>Detentor de Direitos: contacte a Cinemateca Portuguesa.</p>
<p>ID CP-MC: 7000178</p>
<iframe src="http://player.vimeo.com/video/26173904?title=0"></iframe>
<p>© 2013 CINEMATECA PORTUGUESA - Museu do Cinema, IP</p>
</body></html>
"""


class CinematecaPortuguesaCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_portuguese_film_archive(self):
        institutions = collect_cinemateca_portuguesa_institutions()
        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["country"], "Portugal")
        self.assertEqual(institutions[0]["repository_code"], "PT-CINEMATECA")

    def test_parse_video_list_page_extracts_public_records(self):
        records = parse_cinemateca_portuguesa_video_list_page(
            LIST_HTML,
            "https://www.cinemateca.pt/cinemateca-digital/video.aspx",
        )
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["record_id"], "13402")
        self.assertEqual(records[0]["title"], "A Grande Noite do Comércio")
        self.assertEqual(records[0]["date"], "1947")
        self.assertIn("Ficha.aspx?obraid=13402", records[0]["video_link"])

    def test_parse_detail_page_extracts_vimeo_and_metadata(self):
        record = parse_cinemateca_portuguesa_detail_page(
            DETAIL_HTML,
            "https://www.cinemateca.pt/cinemateca-digital/Ficha.aspx?obraid=7947&type=Video",
        )
        self.assertEqual(record["record_id"], "7947")
        self.assertEqual(record["platform"], "Vimeo")
        self.assertIn("player.vimeo.com/video/26173904", record["video_link"])
        self.assertIn("documentário", record["subject"])
        self.assertIn("iframe Vimeo", record["description"])

    def test_theme_and_access_surface_are_specific(self):
        row = {
            "platform": "Cinemateca Digital",
            "video_link": "https://www.cinemateca.pt/cinemateca-digital/Ficha.aspx?obraid=13402&type=Video",
            "video_title": "30 Anos Com Salazar",
            "video_subject": "Portugal, 1947(?)",
            "video_description": "Ficha pública de vídeo na Cinemateca Digital.",
        }
        self.assertEqual(infer_video_theme(row), "Vida pública, política e história")
        self.assertEqual(classify_access_surface(row), "Cinemateca digital institucional")


if __name__ == "__main__":
    unittest.main()
