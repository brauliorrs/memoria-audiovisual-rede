import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.cinematheque_francaise import (
    collect_cinematheque_francaise_institutions,
    parse_cinematheque_francaise_henri_detail,
    parse_cinematheque_francaise_henri_list,
)


class CinemathequeFrancaiseCollectionTests(unittest.TestCase):
    def test_collect_institutions_declares_single_archive(self):
        institutions = collect_cinematheque_francaise_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["institution"], "Cinémathèque française / Musée du cinéma")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_henri_list_excludes_unavailable_films(self):
        html = """
        <li class=film><a href=film/154769-le-cinema-des-origines-auteurs-divers-1889-1912/ rel=prefetch>
          <div class=img-container><div class=duree>20:47</div></div>
          <div class=film-info><div class=titre>Le Cinéma des origines </div><div>Auteurs divers, 1889-1912</div></div></a>
        <li class="film archived"><a href=film/154346-histoire-d-une-chevre-iryna-smyrnova-1995/ rel=prefetch>
          <div class=film-info><div class=titre>Histoire d'une chèvre </div><div>Iryna Smyrnova, 1995</div><div class=end>Film indisponible</div></div></a>
        """
        records = parse_cinematheque_francaise_henri_list(html)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "154769")
        self.assertEqual(records[0]["title"], "Le Cinéma des origines")
        self.assertEqual(records[0]["date"], "1889")
        self.assertEqual(records[0]["subject"], "Auteurs divers")

    def test_parse_henri_detail_extracts_vimeo_embed(self):
        html = """
        <html><head><title>Le Cinéma des origines - HENRI</title></head><body>
          <h1>Le Cinéma des origines dans la collection Will Day</h1>
          <p>Auteurs divers</p>
          <p>Grande-Bretagne - France - États-Unis / 1889-1912 / 20:47 / Silencieux</p>
          <p>Montage de fragments uniques et des films de formats obsolètes.</p>
          <iframe src="https://player.vimeo.com/video/900190070?color=7db3af&texttrack=fr"></iframe>
        </body></html>
        """
        record = parse_cinematheque_francaise_henri_detail(
            html,
            "https://www.cinematheque.fr/henri/film/154769-le-cinema-des-origines/",
        )

        self.assertEqual(record["record_id"], "154769")
        self.assertIn("player.vimeo.com/video/900190070", record["video_link"])
        self.assertEqual(record["date"], "1889")
        self.assertTrue(record["embedded"])

    def test_henri_theme_and_access_are_specific(self):
        row = {
            "platform": "HENRI",
            "video_link": "https://player.vimeo.com/video/900190070",
            "video_title": "Le Cinéma des origines dans la collection Will Day",
            "video_subject": "Auteurs divers; 1889-1912 / Silencieux",
            "video_description": "Film publicado em HENRI, plataforma de streaming gratuito da Cinémathèque française.",
        }

        self.assertEqual(infer_video_theme(row), "Patrimônio cinematográfico e cinefilia")
        self.assertEqual(classify_access_surface(row), "Arquivo audiovisual institucional")


if __name__ == "__main__":
    unittest.main()
