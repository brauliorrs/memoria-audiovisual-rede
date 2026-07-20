import ast
import re
import unittest
from pathlib import Path

from memoria_audiovisual.i18n import (
    DEFAULT_LANGUAGE,
    language_code_from_label,
    t,
    translate_ui_text,
)

UI_METHODS = {
    "title",
    "header",
    "subheader",
    "markdown",
    "caption",
    "info",
    "warning",
    "error",
    "success",
    "write",
    "download_button",
    "link_button",
    "button",
    "selectbox",
    "radio",
    "multiselect",
    "text_input",
    "checkbox",
    "metric",
    "expander",
    "tabs",
}

PORTUGUESE_UI_PATTERN = re.compile(
    r"\b(ainda|não|há|histórico|observações|institucionais|atualização|atualizações|"
    r"unidades|unidade|instituições|instituição|vídeo|vídeos|páginas|analisadas|dados|"
    r"distribuição|estado|estados|exportar|exporta|linha|tempo|rodada|rodadas|sinais|"
    r"possível|extinção|acesso|regime|modalidade|categoria|arquivo|arquivos|fonte|fontes|"
    r"recorte|quadro|tabela|mapeamento|fechamento|europeu|europeia|lacunas|pendências|"
    r"avaliação|verificação|site|domínio|país|países|descrição|situação|selecionados|"
    r"localizado|detectados|curatorial|temas|plataformas)\b",
    re.IGNORECASE,
)

UI_SCAN_ALLOWLIST = {
    "Idioma / Language / Idioma",
    "Abrir",
    "Tema",
    "Plataformas",
    "Continentes",
    "Continente",
}


def _streamlit_ui_strings():
    app_path = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
    source = app_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source)

    def add_text(items, line, method, value, context):
        text = " ".join(str(value).split()).strip()
        if not text or text in UI_SCAN_ALLOWLIST or len(text) < 3:
            return
        if text.startswith("<") or "<div" in context or text.startswith("[Abrir"):
            return
        if PORTUGUESE_UI_PATTERN.search(text):
            items.append((line, method, text))

    items = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in UI_METHODS:
            continue

        method = node.func.attr
        context = ast.get_source_segment(source, node) or ""
        for index, arg in enumerate(node.args):
            if method == "tabs" and isinstance(arg, ast.List):
                for item in arg.elts:
                    if isinstance(item, ast.Constant) and isinstance(item.value, str):
                        add_text(items, node.lineno, method, item.value, context)
                    elif isinstance(item, ast.JoinedStr):
                        for part in item.values:
                            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                                add_text(items, node.lineno, method, part.value.strip(" ()"), context)
                continue
            if index > 1 and method != "metric":
                continue
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                add_text(items, node.lineno, method, arg.value, context)
            elif isinstance(arg, ast.JoinedStr):
                for part in arg.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        add_text(items, node.lineno, method, part.value.strip(" ()"), context)

        for keyword in node.keywords:
            if keyword.arg not in {"label", "help", "placeholder"}:
                continue
            if isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                add_text(items, node.lineno, f"{method}.{keyword.arg}", keyword.value.value, context)
            elif isinstance(keyword.value, ast.JoinedStr):
                for part in keyword.value.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        add_text(items, node.lineno, f"{method}.{keyword.arg}", part.value.strip(" ()"), context)

    return items


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

    def test_public_academic_axis_omits_hidden_affiliation_context(self):
        hidden_terms = ["Valência", "Valencia", "Communication and Media Culture History Research Group"]

        for language in ["pt", "es", "en"]:
            public_text = t("academic_axis_text", language)
            for term in hidden_terms:
                self.assertNotIn(term, public_text)

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

    def test_history_metrics_follow_selected_language_without_partial_words(self):
        labels = [
            "Observações históricas das unidades",
            "Observações históricas institucionais",
            "Sinais globais de possível extinção",
            "Unidades com histórico registrado",
            "Histórico geral",
            "Sinais de possível extinção",
        ]

        spanish = [translate_ui_text(label, "es") for label in labels]
        english = [translate_ui_text(label, "en") for label in labels]

        self.assertEqual(
            [
                "Observaciones históricas de las unidades",
                "Observaciones históricas institucionales",
                "Señales globales de posible extinción",
                "Unidades con historial registrado",
                "Historial general",
                "Señales de posible extinción",
            ],
            spanish,
        )
        self.assertNotIn("Unidads", " ".join(spanish))
        self.assertEqual(
            [
                "Historical Unit Observations",
                "Institutional Historical Observations",
                "Global Signals of Possible Extinction",
                "Units with Registered History",
                "General History",
                "Signals of Possible Extinction",
            ],
            english,
        )

    def test_streamlit_visible_portuguese_fragments_are_covered(self):
        for language in ["es", "en"]:
            with self.subTest(language=language):
                missing = [
                    (line, method, text)
                    for line, method, text in _streamlit_ui_strings()
                    if translate_ui_text(text, language) == text
                ]
                self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
