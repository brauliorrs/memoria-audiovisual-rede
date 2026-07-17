import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinememoire import (
    build_cinememoire_list_url,
    collect_cinememoire_institutions,
    parse_cinememoire_list_page,
    parse_cinememoire_notice_page,
)


LIST_HTML = """
<html><body>
  <p>Repas familial Séquence 001-001 3' 30'' Super 8 Muet - Couleur
    <a href="notice?num_seq=2873">Voir la notice</a>
  </p>
  <p>Nice, carnaval Séquence 284-048 6' 28''
    <a href="https://cinememoire.net/notice?num_seq=875">Voir la notice</a>
  </p>
</body></html>
"""


NOTICE_HTML = """
<html>
<head>
  <title>Repas de famille en sous bois</title>
  <meta property="og:title" content="Repas de famille en sous bois">
  <meta property="og:description" content="Un repas familial dans une maison de campagne.">
  <meta name="keywords" content="Famille, Super 8, Film amateur">
</head>
<body>
  <video controls poster="/streaming/cinememoire/sequences/001-001-Streaming.jpg">
    <source src="/streaming/cinememoire/sequences/001-001-Streaming.mp4" type="video/mp4">
  </video>
  Télécharger la séquence
  Repas de famille en sous bois
  Séquence 001-001
  3' 30''
  Super 8
  Muet - Couleur
  Déposant
  385
  Dépôt
  1
  Date :
  1976
  1977
  Géographie :
  France
  Bouches-du-Rhône-13
  Genre :
  Document brut
  Film de famille
  Toponymie :
  Campagne
  Descripteurs :
  Famille étendue
</body>
</html>
"""


class CinememoireCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_cinememoire_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémémoire")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_build_list_url_uses_public_search_pagination(self):
        self.assertEqual(build_cinememoire_list_url(3), "https://cinememoire.net/recherche-simple?p=3")

    def test_parse_list_page_extracts_notice_links(self):
        records = parse_cinememoire_list_page(LIST_HTML, page_number=2)

        self.assertEqual([record["record_id"] for record in records], ["2873", "875"])
        self.assertEqual(records[0]["page_number"], 2)
        self.assertEqual(records[0]["page_url"], "https://cinememoire.net/notice?num_seq=2873")

    def test_parse_notice_page_extracts_public_mp4_and_metadata(self):
        row = parse_cinememoire_notice_page(NOTICE_HTML, "https://cinememoire.net/notice?num_seq=2873")

        self.assertEqual(row["record_id"], "2873")
        self.assertEqual(row["platform"], "Cinémémoire")
        self.assertTrue(row["video_link"].endswith("/001-001-Streaming.mp4"))
        self.assertIn("Film de famille", row["subject"])
        self.assertIn("duração: 3' 30''", row["description"])
        self.assertEqual(infer_video_theme(row), "Filme amador e memória familiar")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
