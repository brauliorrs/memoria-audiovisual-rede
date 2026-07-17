import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.ciclic import (
    collect_ciclic_institutions,
    parse_ciclic_film_page,
    parse_ciclic_list_page,
)


class CiclicCollectionTests(unittest.TestCase):
    def test_collect_ciclic_institutions_declares_single_archive(self):
        institutions = collect_ciclic_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "FR-CICLIC")
        self.assertEqual(institutions[0]["country"], "France")

    def test_parse_ciclic_list_page_extracts_public_film_records(self):
        html = """
        <div id="afficher_plusciclic_memoire_liste_films">
          <div class="block-item">
            <a href="/27298-histoire-d-otage-fiction">
              Histoire d'ô...Tage [Fiction]
            </a>
          </div>
        </div>
        """

        records = parse_ciclic_list_page(html, page_number=0)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "27298")
        self.assertEqual(records[0]["page_url"], "https://memoire.ciclic.fr/27298-histoire-d-otage-fiction")
        self.assertIn("Histoire", records[0]["list_text"])

    def test_parse_ciclic_film_page_extracts_embed_and_analytic_fields(self):
        html = """
        <article class="node-film">
          <h1>Histoire d'ô...Tage [Fiction]</h1>
          <div class="node-film-header">
            1976 Réalisé par : Maurice Huvelin En ligne le 16 Jun 2026 Saint-Jean-le-Blanc (45)
          </div>
          <iframe src="/embed/27298?title=0"></iframe>
          <p>Fiction tournée en 16 mm dans le Loiret.</p>
        </article>
        """
        embed_html = """
        <video>
          <source src="https://medias.ciclic.fr/dash/27298/stream.mpd" type="application/dash+xml">
          <source src="https://medias.ciclic.fr/dash/27298/master.m3u8" type="application/x-mpegURL">
        </video>
        """

        record = parse_ciclic_film_page(
            html,
            "https://memoire.ciclic.fr/27298-histoire-d-otage-fiction",
            embed_html,
        )

        self.assertEqual(record["record_id"], "27298")
        self.assertEqual(record["video_link"], "https://medias.ciclic.fr/dash/27298/master.m3u8")
        self.assertEqual(record["platform"], "Ciclic Mémoire")
        self.assertEqual(record["date"], "1976")
        self.assertIn("Maurice Huvelin", record["description"])
        self.assertTrue(record["embedded"])

        analytic_row = {
            "platform": record["platform"],
            "video_link": record["video_link"],
            "video_title": record["title"],
            "video_subject": record["subject"],
            "video_description": record["description"],
        }
        self.assertEqual(infer_video_theme(analytic_row), "Ficção cinematográfica")
        self.assertEqual(classify_access_surface(analytic_row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
