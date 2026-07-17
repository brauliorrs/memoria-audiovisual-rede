import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cna import (
    collect_cna_institutions,
    extract_cna_declared_pages,
    extract_cna_result_total,
    parse_cna_detail_page,
    parse_cna_result_page,
)


class CnaCollectionTests(unittest.TestCase):
    def test_collect_cna_institutions_declares_luxembourg_archive(self):
        institutions = collect_cna_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "LU-CNA")
        self.assertEqual(institutions[0]["country"], "Luxembourg")

    def test_parse_cna_result_page_extracts_film_detail_links(self):
        html = """
        <main>
          <p>Images animées et enregistrements audio 79 Résultats</p>
          <a href="/resultsnavigate/6">6</a>
          <a href="https://cnasearch.public.lu/Details/film/150015551">
            Roi Baudouin 1er au Grand-Duché du Luxembourg
          </a>
          <a href="/Details/film/150018471">tour du Luxembourg 1946 en 4 étapes</a>
        </main>
        """

        records = parse_cna_result_page(html, "https://cnasearch.public.lu/results")

        self.assertEqual(extract_cna_result_total(html), 79)
        self.assertEqual(extract_cna_declared_pages(html), 6)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["record_id"], "150015551")
        self.assertIn("/Details/film/150018471", records[1]["page_url"])

    def test_parse_cna_detail_page_extracts_metadata_and_mp4_source(self):
        html = """
        <main>
          <h1>Roi Baudouin 1er au Grand-Duché du Luxembourg</h1>
          <video class="video-player" controls="controls">
            <source src="https://cna.kiss.lu/getMedium/b94401142380e6c35499e8058e388426" type="video/mp4"/>
          </video>
          <p>
            Média
            Numéro d’objet IA_DOC_001265
            Titre Le Roi Baudouin 1er au Grand-Duché du Luxembourg (Titre privilégié)
            Genre Films documentaires
            Description détaillée Reportage sur la visite du roi des Belges Baudouin 1er.
            Synopsis (résumé) Reportage sur la visite officielle.
            Date 1959-06-16 (Date de production)
            Pays Luxembourg
            Crédits Philippe Schneider (1908-1980) (Réalisateur)
            Sujet Visites officielles
            Mot-clé géographique Luxembourg (Luxembourg)
            Forme Courts métrages, Films documentaires
            Langue du contenu français
            Nature du document Image animée
            Navigateur hiérarchique IA_DOC_001265
          </p>
        </main>
        """

        record = parse_cna_detail_page(html, "https://cnasearch.public.lu/Details/film/150015551")

        self.assertEqual(record["record_id"], "150015551")
        self.assertEqual(record["platform"], "CNAsearch")
        self.assertEqual(record["date"], "1959")
        self.assertEqual(record["video_link"], "https://cna.kiss.lu/getMedium/b94401142380e6c35499e8058e388426")
        self.assertIn("número de objeto: IA_DOC_001265", record["description"])
        self.assertTrue(record["embedded"])
        self.assertTrue(record["is_moving_image"])

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Vida pública, política e história")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")

    def test_cna_theme_prefers_title_and_subject_over_accessory_description(self):
        industrial_row = {
            "platform": "CNAsearch",
            "video_title": "La centrale de Vianden",
            "video_subject": "Centrales hydroélectriques de pompage Énergie hydraulique Construction Électricité",
            "video_description": "créditos: grande-duchesse | fonte de mídia: video/mp4",
        }
        public_row = {
            "platform": "CNAsearch",
            "video_title": "Roi Baudouin 1er au Grand-Duché du Luxembourg",
            "video_subject": "Visites officielles; Luxembourg",
            "video_description": "natureza: Image animée",
        }

        self.assertEqual(infer_video_theme(industrial_row), "Trabalho, indústria e infraestrutura")
        self.assertEqual(infer_video_theme(public_row), "Vida pública, política e história")


if __name__ == "__main__":
    unittest.main()
