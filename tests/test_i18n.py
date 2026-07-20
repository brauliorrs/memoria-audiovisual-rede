import unittest

from memoria_audiovisual.i18n import (
    DEFAULT_LANGUAGE,
    language_code_from_label,
    t,
    translate_ui_text,
)


class I18nTests(unittest.TestCase):
    def test_language_code_from_label_defaults_to_portuguese(self):
        self.assertEqual(language_code_from_label("English"), "en")
        self.assertEqual(language_code_from_label("Español"), "es")
        self.assertEqual(language_code_from_label("desconhecido"), DEFAULT_LANGUAGE)

    def test_core_project_labels_are_available_in_three_languages(self):
        self.assertEqual(
            t("app_title", "pt"),
            "Plataforma aberta de curadoria e acesso à memória audiovisual em rede",
        )
        self.assertIn("memoria audiovisual", t("app_title", "es"))
        self.assertIn("audiovisual memory", t("app_title", "en"))

    def test_common_ui_phrases_are_translated_without_changing_internal_values(self):
        self.assertEqual(translate_ui_text("Todas as unidades", "es"), "Todas las unidades")
        self.assertEqual(translate_ui_text("Todas as unidades", "en"), "All units")
        self.assertEqual(translate_ui_text("Todas as unidades", "pt"), "Todas as unidades")

    def test_section_subtitles_follow_selected_language(self):
        source = (
            "Este quadro acompanha a saúde temporal do observatório por unidade documental,\n"
            "distinguindo atualizações recentes, pendências de rodadas parciais e atrasos de acompanhamento."
        )

        self.assertIn("salud temporal", translate_ui_text(source, "es"))
        self.assertIn("temporal health", translate_ui_text(source, "en"))


if __name__ == "__main__":
    unittest.main()
