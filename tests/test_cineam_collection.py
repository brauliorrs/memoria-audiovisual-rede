import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cineam import (
    collect_cineam_institutions,
    parse_cineam_film_page,
    parse_cineam_list_page,
)


class CineamCollectionTests(unittest.TestCase):
    def test_collect_cineam_institutions_declares_single_archive(self):
        institutions = collect_cineam_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "FR-CINEAM")
        self.assertEqual(institutions[0]["country"], "France")

    def test_parse_cineam_list_page_extracts_public_records(self):
        html = """
        <article class="diaListItem" data-diaref="-3818"
          onclick="document.location.href='exploration-moulins-905-0-0-0.html?_doc=9%3A4%3A3818&amp;page=1'">
          <img src="https://diazcineam.oembed.diazinteregio.org/thumb/v/STOJANOVIC/0302FI0022.jpg">
          Moulins, nichoirs et anniversaire 1976 | Dušanka STOJANOVIC
        </article>
        """

        records = parse_cineam_list_page(html, "https://www.cineam.asso.fr/exploration-905-0-0-0.html")

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "3818")
        self.assertIn("_doc=9%3A4%3A3818", records[0]["page_url"])
        self.assertEqual(records[0]["title"], "Moulins, nichoirs et anniversaire")
        self.assertEqual(records[0]["date"], "1976")

    def test_parse_cineam_film_page_extracts_embed_and_analytic_fields(self):
        html = """
        <main>
          <h1>Exploration</h1>
          <h1>Moulins, nichoirs et anniversaire</h1>
          <p>Réalisation Dušanka STOJANOVIC Année 1976 Format Film super 8
          Son Muet Coloration Couleur Durée 00:03:25
          Ajouter à mes sélections Envoyer un commentaire Instrument de musique Accordéon Repas de famille
          Résumé La famille visite une exposition de moulins à vent pendant un anniversaire.
          Suggestions Ici les suggestions...</p>
          <iframe src="https://diazcineam.oembed.diazinteregio.org/embed/STOJANOVIC/0302FI0022?feature=oembed"></iframe>
        </main>
        """
        embed_html = """
        <video>
          <source src="/video/STOJANOVIC/0302FI0022.mp4" type="video/mp4">
        </video>
        """

        record = parse_cineam_film_page(
            html,
            "https://www.cineam.asso.fr/exploration-moulins-905-0-0-0.html?_doc=9%3A4%3A3818&page=1",
            embed_html,
        )

        self.assertEqual(record["record_id"], "3818")
        self.assertEqual(
            record["video_link"],
            "https://diazcineam.oembed.diazinteregio.org/video/STOJANOVIC/0302FI0022.mp4",
        )
        self.assertEqual(record["platform"], "CINÉAM")
        self.assertEqual(record["date"], "1976")
        self.assertIn("duração: 00:03:25", record["description"])
        self.assertIn("descritores: Instrument de musique", record["description"])
        self.assertNotIn("Ajouter à mes sélections", record["description"])
        self.assertNotIn("Envoyer un commentaire", record["description"])
        self.assertIn("Dušanka STOJANOVIC", record["description"])
        self.assertTrue(record["embedded"])

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Filme amador e memória familiar")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")

    def test_cineam_theme_rules_distinguish_daily_life_and_territory(self):
        daily_life = {
            "platform": "CINÉAM",
            "video_title": "Écoles - Danse - Théâtre - Sorties - Karting",
            "video_subject": "Brétigny-sur-Orge (91)",
            "video_description": "kermesse et fête scolaire",
        }
        territory = {
            "platform": "CINÉAM",
            "video_title": "Porte d'Auteuil - Construction du Pont Garigliano",
            "video_subject": "Paris (75) Pont Construction d'ouvrage d'art",
            "video_description": "construction du pont",
        }

        self.assertEqual(infer_video_theme(daily_life), "Documentário, cotidiano e memória local")
        self.assertEqual(infer_video_theme(territory), "Território, cidade e memória local")

    def test_parse_cineam_film_page_trims_interface_tail_without_suggestions(self):
        html = """
        <main>
          <h1>Exploration</h1>
          <h1>Fête locale</h1>
          <p>Réalisation Auteur Année 1960 Format Film 8 mm Son Muet
          Coloration Noir et blanc Durée 00:02:00 Résumé Défilé et kermesse dans une commune.
          Suggestions Ici les suggestions Sauvegarder ma recherche Nom de votre recherche sauvegardée
          Votre recherche sauvegardée Fermer Choix de la sélection Nouvelle sélection
          Envoyer un commentaire Recherche avancée Inscrivez-vous à la newsletter</p>
        </main>
        """

        record = parse_cineam_film_page(html, "https://www.cineam.asso.fr/fiche.html?_doc=9%3A4%3A1234")

        self.assertIn("Défilé et kermesse dans une commune.", record["description"])
        self.assertNotIn("Suggestions Ici les suggestions", record["description"])
        self.assertNotIn("Sauvegarder ma recherche", record["description"])
        self.assertNotIn("Votre recherche sauvegardée", record["description"])
        self.assertNotIn("Envoyer un commentaire", record["description"])


if __name__ == "__main__":
    unittest.main()
