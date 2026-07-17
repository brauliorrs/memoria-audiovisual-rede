import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cpsa import (
    collect_cpsa_institutions,
    extract_cpsa_declared_pages,
    extract_cpsa_declared_total,
    parse_cpsa_detail_page,
    parse_cpsa_list_page,
)


class CpsaCollectionTests(unittest.TestCase):
    def test_collect_cpsa_institutions_declares_single_archive(self):
        institutions = collect_cpsa_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque des Pays de Savoie et de l'Ain")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_list_page_extracts_public_records(self):
        html = """
        <main>
          <p>1593 film(s)</p>
          <a href="le-catalogue-des-collections-527-0-0-133.html?">133</a>
          <ul>
            <li class="nouvelleCont">
              <a href="le-catalogue-des-collections-527-9859-0-0.html?" title="Annecy couleur">Annecy couleur</a>
              <p>Philippe BONNOT 1967 Ajouter à ma sélection</p>
            </li>
          </ul>
        </main>
        """
        records = parse_cpsa_list_page(html, "https://www.letelepherique.org/le-catalogue-des-collections-527-0-0-0.html")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "9859")
        self.assertEqual(records[0]["title"], "Annecy couleur")
        self.assertEqual(records[0]["date"], "1967")
        self.assertEqual(extract_cpsa_declared_total(html), 1593)
        self.assertEqual(extract_cpsa_declared_pages(html), 133)

    def test_parse_detail_page_extracts_embed_and_metadata(self):
        html = """
        <html>
          <head>
            <title>Annecy couleur - Philippe BONNOT - 1967 - Le Catalogue des Collections</title>
            <meta property="og:image" content="https://diazcpsa.oembed.diazinteregio.org/thumb/v/0620_0629/0626/06260001_480.jpg">
          </head>
          <body>
            <h1>Annecy couleur</h1>
            <a href="https://diazcpsa.oembed.diazinteregio.org/embed/0620_0629/0626/06260001_480?feature=oembed">voir</a>
            <p>Synopsis : Carton Annecy ses vieux quartiers</p>
            <p>Réalisation : Philippe BONNOT</p>
            <p>Date : 1967 précisément</p>
            <p>Lieu(x) : Annecy (74)</p>
            <p>Descripteurs : Lac naturel</p>
            <p>Format : Film 9,5 mm</p>
            <p>Son : Muet</p>
            <p>Durée : 00:04:12</p>
          </body>
        </html>
        """
        record = parse_cpsa_detail_page(html, "https://www.letelepherique.org/le-catalogue-des-collections-527-9859-0-0.html")

        self.assertEqual(record["record_id"], "9859")
        self.assertIn("diazcpsa.oembed", record["video_link"])
        self.assertEqual(record["date"], "1967")
        self.assertTrue(record["embedded"])
        self.assertIn("Philippe BONNOT", record["subject"])
        self.assertIn("duração: 00:04:12", record["description"])

    def test_cpsa_theme_and_access_are_specific(self):
        row = {
            "platform": "Cinémathèque des Pays de Savoie et de l'Ain",
            "video_link": "https://diazcpsa.oembed.diazinteregio.org/embed/0620_0629/0626/06260001_480",
            "video_title": "Annecy couleur",
            "video_subject": "Annecy (74); Lac naturel",
            "video_description": "Memória local, paisagem e vida urbana nos Alpes.",
        }

        self.assertEqual(infer_video_theme(row), "Território, cidade e memória local")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
