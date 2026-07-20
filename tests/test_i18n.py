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

    def test_empty_state_messages_are_not_partially_translated(self):
        source = "Ainda não há dados suficientes para cruzar temas e países."

        self.assertEqual(
            translate_ui_text(source, "es"),
            "Todavía no hay datos suficientes para cruzar temas y países.",
        )
        self.assertEqual(
            translate_ui_text(source, "en"),
            "There is not enough data yet to cross themes and countries.",
        )

    def test_methodological_warnings_follow_selected_language(self):
        source = "O site respondeu com restrição de acesso. Para o projeto, ele entra como não disponível."

        self.assertIn("restricción de acceso", translate_ui_text(source, "es"))
        self.assertIn("access restrictions", translate_ui_text(source, "en"))

    def test_internal_tab_labels_follow_selected_language(self):
        tab_labels = [
            "Histórico geral",
            "Sinais de possível extinção",
            "Critérios de fechamento",
            "Ficha e acesso",
            "Vídeos detectados (12)",
            "Páginas analisadas (3)",
        ]

        spanish = [translate_ui_text(label, "es") for label in tab_labels]
        english = [translate_ui_text(label, "en") for label in tab_labels]

        self.assertIn("Historial general", spanish)
        self.assertIn("Señales de posible extinción", spanish)
        self.assertIn("Closure Criteria", english)
        self.assertIn("Record and Access", english)
        self.assertIn("Detected Videos (12)", english)
        self.assertIn("Analyzed Pages (3)", english)


if __name__ == "__main__":
    unittest.main()
