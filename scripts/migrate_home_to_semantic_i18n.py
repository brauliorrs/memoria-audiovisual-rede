from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "app" / "streamlit_app.py"
PT_PATH = ROOT / "src" / "memoria_audiovisual" / "locales" / "pt.json"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def main() -> None:
    app = APP_PATH.read_text(encoding="utf-8-sig")

    app = replace_once(
        app,
        "from memoria_audiovisual.i18n import (\n"
        "    DEFAULT_LANGUAGE,\n"
        "    LANGUAGE_OPTIONS,\n"
        "    language_code_from_label,\n"
        "    t,\n"
        "    translate_ui_text,\n"
        ")\n",
        "from memoria_audiovisual.i18n import (\n"
        "    DEFAULT_LANGUAGE,\n"
        "    LANGUAGE_OPTIONS,\n"
        "    language_code_from_label,\n"
        "    t,\n"
        "    translate_ui_text,\n"
        ")\n"
        "from memoria_audiovisual.locale_catalog import translate_key\n",
        "locale catalogue import",
    )

    app = replace_once(
        app,
        "APP_LANGUAGE = render_language_selector()\n"
        "install_streamlit_i18n(APP_LANGUAGE)\n"
        "st.sidebar.caption(tr(\"language_note\"))\n"
        "st.sidebar.caption(tr(\"raw_data_note\"))\n",
        "# The multilingual selector remains disabled during the semantic-catalogue migration.\n"
        "# Portuguese is the sole active interface language until the English catalogue is rebuilt.\n"
        "APP_LANGUAGE = DEFAULT_LANGUAGE\n",
        "disable language selector",
    )

    app = replace_once(
        app,
        "def tr(key, **kwargs):\n"
        "    return t(key, APP_LANGUAGE, **kwargs)\n",
        "def tr(key, **kwargs):\n"
        "    return t(key, APP_LANGUAGE, **kwargs)\n\n\n"
        "def tr_key(key, **kwargs):\n"
        "    return translate_key(key, APP_LANGUAGE, **kwargs)\n",
        "semantic translation helper",
    )

    replacements = {
        'st.title(tr("app_title"))': 'st.title(tr_key("home.title"))',
        'st.caption(tr("app_caption"))': 'st.caption(tr_key("home.caption"))',
        '            "Pesquisa global",\n            placeholder="Pesquisar no acervo audiovisual",': '            tr_key("home.search.label"),\n            placeholder=tr_key("home.search.placeholder"),',
        '            "Pesquisar",\n            type="primary",': '            tr_key("home.search.button"),\n            type="primary",',
        '                "Fechar pesquisa",\n                use_container_width=True,': '                tr_key("home.search.close"),\n                use_container_width=True,',
        '[localize_ui("Visão geral")]': '[tr_key("navigation.overview")]',
        '[tr("category_tab", label=localize_ui(category_def["short_label"])) for category_def in CORPUS_CATEGORIES.values()]': '[tr_key("navigation.category", label=category_def["short_label"]) for category_def in CORPUS_CATEGORIES.values()]',
        '[tr("unit_tab", label=definition["short_label"]) for definition in CORPORA.values()]': '[tr_key("navigation.unit", label=definition["short_label"]) for definition in CORPORA.values()]',
        '[tr("documented_case_tab", label=unit["unit_label"]) for unit in protocolled_excluded_units]': '[tr_key("navigation.documented_case", label=unit["unit_label"]) for unit in protocolled_excluded_units]',
    }
    for old, new in replacements.items():
        app = replace_once(app, old, new, old[:60])

    APP_PATH.write_text(app, encoding="utf-8")

    catalogue = json.loads(PT_PATH.read_text(encoding="utf-8"))
    catalogue.update(
        {
            "home.title": "Plataforma aberta de observação da memória audiovisual em rede",
            "home.caption": "O observatório funciona como plataforma científica aberta para mapear visibilidade, acesso, interoperabilidade e possíveis retrações digitais de acervos audiovisuais.",
            "home.search.label": "Pesquisa global",
            "home.search.placeholder": "Pesquisar no acervo audiovisual",
            "home.search.button": "Pesquisar",
            "home.search.close": "Fechar pesquisa",
            "navigation.overview": "Visão geral",
            "navigation.category": "Categoria: {label}",
            "navigation.unit": "Unidade: {label}",
            "navigation.documented_case": "Caso registrado: {label}",
        }
    )
    PT_PATH.write_text(json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
