import unittest

from memoria_audiovisual.analysis import classify_access_surface, infer_video_theme
from memoria_audiovisual.ecpad import collect_ecpad_institutions, parse_ecpad_search_results


class ECPADCollectionTests(unittest.TestCase):
    def test_collect_ecpad_institutions_declares_single_archive(self):
        institutions = collect_ecpad_institutions()

        self.assertEqual(len(institutions), 1)
        self.assertEqual(institutions[0]["repository_code"], "FR-ECPAD")
        self.assertTrue(institutions[0]["content_available_in_source"])

    def test_parse_ecpad_search_results_extracts_public_video_card(self):
        html = """
        <div class="resultat_container resultat_mosaique type-vidéo visibilite-visible-front">
          <a href="/archives/consulter-les-archives-en-ligne?detail=9620" data-detail="9620"></a>
          <span data-champ="reference">D1020-FILM-001</span>
          <span data-champ="titre">Fonds cinématographique relatif à la guerre d'Algérie</span>
          <span data-champ="resumeint">Descriptif succinct : parachutistes, soldats et paysages d'Algérie.</span>
        </div>
        """

        records = parse_ecpad_search_results(html, online_visual=True)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["record_id"], "9620")
        self.assertIn("visual_online=true", records[0]["description"])
        self.assertEqual(records[0]["platform"], "ECPAD Archives")
        self.assertTrue(records[0]["embedded"])

    def test_parse_ecpad_search_results_marks_video_without_online_visual(self):
        html = """
        <div class="resultat_container resultat_mosaique type-vidéo visibilite-visible-front">
          <a href="/archives/consulter-les-archives-en-ligne?detail=9353" data-detail="9353"></a>
          <span data-champ="reference">2017_ECPAD_TO_152_M_RU_065_V1</span>
          <span data-champ="titre">Entretien d'un canon CAESAR.</span>
          <span data-champ="resumeint">Nettoyage d'un canon CAESAR à Erbil le 18/09/2017.</span>
        </div>
        """

        records = parse_ecpad_search_results(html, online_visual=False)

        self.assertEqual(len(records), 1)
        self.assertIn("visual_online=false", records[0]["description"])
        self.assertEqual(records[0]["date"], "2017-09-18")
        self.assertFalse(records[0]["embedded"])

    def test_ecpad_theme_and_access_are_specific(self):
        public_row = {
            "platform": "ECPAD Archives",
            "video_title": "Entretien d'un canon CAESAR",
            "video_subject": "référence: 2017_ECPAD",
            "video_description": "media_type=video; visual_online=true. Maintenance et armement.",
            "video_link": "https://archives.ecpad.fr/archives/consulter-les-archives-en-ligne?detail=1",
        }
        restricted_row = dict(public_row)
        restricted_row["video_description"] = "media_type=video; visual_online=false. Consultation en salle."

        self.assertEqual(infer_video_theme(public_row), "Tecnologia, armamentos e infraestrutura militar")
        self.assertEqual(classify_access_surface(public_row), "Arquivo audiovisual institucional")
        self.assertEqual(
            classify_access_surface(restricted_row),
            "Metadados audiovisuais públicos com mídia local/autorizada",
        )


if __name__ == "__main__":
    unittest.main()
