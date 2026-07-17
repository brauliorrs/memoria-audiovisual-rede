import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinematheque_bretagne import (
    collect_cinematheque_bretagne_institutions,
    extract_cinematheque_bretagne_declared_free_total,
    extract_cinematheque_bretagne_declared_list_total,
    extract_cinematheque_bretagne_declared_pages,
    parse_cinematheque_bretagne_detail_page,
    parse_cinematheque_bretagne_list_page,
)


class CinemathequeBretagneCollectionTests(unittest.TestCase):
    def test_collect_cinematheque_bretagne_institutions_declares_single_archive(self):
        institutions = collect_cinematheque_bretagne_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque de Bretagne")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_list_page_extracts_public_records(self):
        html = """
        <main>
          <p>11 186 Films en accès libre</p>
          <p>[ 1-15 / 37682 ]</p>
          <a href="voir-les-films-426-0-0-10.html?">10</a>
          <ul class="list">
            <li class="nouvelleCont_000316">
              <div id="empV1_dll_000316_426__50585">
                <a href="voir-les-films-entretien-426-50585-0-1.html?" title="Entretien">Entretien</a>
                <div class="reaAnnee"><h3>2026 | Alice AUDINET | Rose LAGADEC</h3></div>
                <div class="PABret">Film amateur | Bretagne</div>
                <div class="Resume"><p>Mémoire de la cinémathèque.</p></div>
              </div>
            </li>
          </ul>
        </main>
        """
        records = parse_cinematheque_bretagne_list_page(
            html,
            "https://www.cinematheque-bretagne.bzh/voir-les-films-426-0-0-0.html",
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "50585")
        self.assertEqual(records[0]["title"], "Entretien")
        self.assertEqual(records[0]["date"], "2026")
        self.assertEqual(records[0]["subject"], "Alice AUDINET | Rose LAGADEC; Film amateur | Bretagne")
        self.assertEqual(records[0]["platform"], "Cinémathèque de Bretagne")
        self.assertEqual(extract_cinematheque_bretagne_declared_free_total(html), 11186)
        self.assertEqual(extract_cinematheque_bretagne_declared_list_total(html), 37682)
        self.assertEqual(extract_cinematheque_bretagne_declared_pages(html), 10)

    def test_parse_detail_page_extracts_embed_and_metadata(self):
        html = """
        <html>
          <head><title>Entretien - Voir les films</title></head>
          <body>
            <div class="ficheTitle">
              <h2>Entretien <a>Alice AUDINET</a> | <a>Rose LAGADEC</a></h2>
            </div>
            <div class="PABret">Film amateur | Bretagne</div>
            <iframe src="https://diazcdb.oembed.diazinteregio.org/embed/50585?feature=oembed"></iframe>
            <div class="mainCd">
              <ul>
                <li class="diaduree"><ul><li>Durée</li><li>00:17:12</li></ul></li>
                <li class="diacoloration_id"><ul><li>Coloration</li><li>Couleur</li></ul></li>
                <li class="diaformat_origine_id"><ul><li>Format original</li><li>Fichier numérique</li></ul></li>
                <li class="diason_id"><ul><li>Son</li><li>Sonore</li></ul></li>
              </ul>
            </div>
            <div class="sSection resume actif" id="section_resume">
              <div class="sectionTitle">Résumé</div>
              <div class="sectionBody"><div class="Resume"><p>Entretien realizado em 2026 em Brest.</p></div></div>
            </div>
          </body>
        </html>
        """
        record = parse_cinematheque_bretagne_detail_page(
            html,
            "https://www.cinematheque-bretagne.bzh/voir-les-films-entretien-426-50585-0-1.html",
        )

        self.assertEqual(record["record_id"], "50585")
        self.assertEqual(record["video_link"], "https://diazcdb.oembed.diazinteregio.org/embed/50585?feature=oembed")
        self.assertEqual(record["date"], "2026")
        self.assertTrue(record["embedded"])
        self.assertIn("Film amateur | Bretagne", record["subject"])
        self.assertIn("duração: 00:17:12", record["description"])

    def test_cinematheque_bretagne_theme_and_access_are_specific(self):
        row = {
            "platform": "Cinémathèque de Bretagne",
            "video_link": "https://diazcdb.oembed.diazinteregio.org/embed/50585",
            "video_title": "Films scolaires de Douarnenez - Marée noire",
            "video_subject": "Film amateur | Bretagne",
            "video_description": "Memória marítima e escolar na Bretanha.",
        }

        self.assertEqual(infer_video_theme(row), "Território, cidade e memória local")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
